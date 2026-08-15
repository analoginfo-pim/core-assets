<#
.SYNOPSIS
  Multi-signal stuck-agent scanner (transcript + lease + process). Hidden-safe.

.DESCRIPTION
  Replaces mtime-only idle. Signals (all evaluated):

  A) Transcript event kind — last tool_use vs thinking/text-only vs turn_ended
  B) Dead-man lease from Cursor hooks (progress_idx vs thought_idx)
  C) Cross-tick progress (tool_count unchanged while still running)
  D) Cursor helper CPU sample (hung process section; never auto-interrupt)

  Sources: ClawGuard stuck-tool, Antigravity step_idx, OpenClaw isolated
  heartbeat, Healthchecks.io / Crontap dead-man. See README-local-watcher.md.

  Never interrupt-queues IDs that have turn_ended/success (UI ghosts).
  Never interrupt-queues the NeverInterruptPrefixes list.
#>
[CmdletBinding()]
param(
    [double]$PlanningStallMinutes = 3.5,
    [double]$IdleMinutes = 4,
    [double]$LiveStuckMaxAgeMinutes = 240,
    [double]$GhostWindowHours = 6,
    [string]$TranscriptRoot = 'C:\Users\phil\.cursor\projects\c-analog-pim\agent-transcripts',
    [string]$StateDir = '',
    [string[]]$NeverInterruptPrefixes = @(
        '5516df5e', '873476da', 'e766aa3a', '8e2dd3b8'
    ),
    [switch]$NoEmitInterruptRequests,
    [switch]$NoSlack
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $StateDir) {
    $StateDir = Join-Path $PSScriptRoot 'local-watcher-state'
}

$queueDir = Join-Path $StateDir 'interrupt-queue'
$leaseDir = Join-Path $StateDir 'leases'
$reportPath = Join-Path $StateDir 'latest-report.md'
$jsonPath = Join-Path $StateDir 'latest-report.json'
$signalPath = Join-Path $StateDir 'PARENT-SIGNAL.md'
$statusPath = Join-Path $StateDir 'status.json'
$notifiedPath = Join-Path $StateDir 'notified-ids.json'
$progressPath = Join-Path $StateDir 'progress-state.json'
$procSamplePath = Join-Path $StateDir 'process-sample.json'
$slackScript = Join-Path $PSScriptRoot 'Send-AgentSlack.ps1'

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
New-Item -ItemType Directory -Force -Path $queueDir | Out-Null
New-Item -ItemType Directory -Force -Path $leaseDir | Out-Null

$stopPlanning = @'
STOP PLANNING. Deliver NOW from what you already know.
Return a short DONE checklist (done / deferred / blocked) for THIS slice only.
No more exploration, no more Read/Grep loops, no more planning.
If you lack facts, mark blocked with the one smallest missing path - then stop.
'@

function Test-NeverInterrupt([string]$Id) {
    $short = $Id
    if ($short.Length -gt 8) { $short = $short.Substring(0, 8) }
    foreach ($p in $NeverInterruptPrefixes) {
        if ($Id.StartsWith($p, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
        if ($short -eq $p) { return $true }
    }
    return $false
}

function Get-JsonMap([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return @{} }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($raw)) { return @{} }
        $obj = $raw | ConvertFrom-Json
        $map = @{}
        foreach ($p in $obj.PSObject.Properties) {
            $map[$p.Name] = $p.Value
        }
        return $map
    }
    catch {
        Write-Warning "Could not parse $(Split-Path -Leaf $Path); starting fresh. $_"
        return @{}
    }
}

function Save-JsonMap([hashtable]$Map, [string]$Path) {
    $obj = [ordered]@{}
    foreach ($key in @($Map.Keys | Sort-Object)) {
        $obj[$key] = $Map[$key]
    }
    $json = ($obj | ConvertTo-Json -Depth 8)
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding $false))
}

function Read-JsonlLines([string]$Path) {
    $lines = [System.Collections.Generic.List[string]]::new()
    try {
        $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $sr = New-Object System.IO.StreamReader($fs)
            try {
                while ($null -ne ($line = $sr.ReadLine())) {
                    [void]$lines.Add($line)
                }
            }
            finally { $sr.Dispose() }
        }
        finally { $fs.Dispose() }
    }
    catch {
        foreach ($l in @(Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
            [void]$lines.Add($l)
        }
    }
    # Comma prevents PowerShell unwrapping a 1-line file to a bare string
    # (StrictMode then fails on $lines.Count).
    return ,$lines
}

function Get-TranscriptSignals {
    param(
        [string]$Path,
        [hashtable]$PriorProgress
    )

    $item = Get-Item -LiteralPath $Path
    $lines = Read-JsonlLines -Path $Path
    if ($lines.Count -eq 0) { return $null }

    $toolCount = 0
    $mutating = 0
    $readOnly = 0
    $lastKind = 'unknown'
    $lastToolName = ''
    $turnEnded = $false
    $turnSuccess = $false
    $aborted = $false
    $lastIsToolUse = $false
    $consecutiveSameTool = 0
    $prevTool = ''
    $maxSameTool = 0
    $assistantTextOnlyTail = 0
    $sawAssistant = $false

    foreach ($line in $lines) {
        if ($line -match '"type"\s*:\s*"turn_ended"') {
            $turnEnded = $true
            $lastKind = 'ended'
            $lastIsToolUse = $false
            if ($line -match '"status"\s*:\s*"success"') { $turnSuccess = $true }
            if ($line -match '"status"\s*:\s*"aborted"') { $aborted = $true }
            continue
        }
        if ($line -match '"status"\s*:\s*"aborted"') { $aborted = $true }

        $toolMatches = [regex]::Matches($line, '"type"\s*:\s*"tool_use"[^}]*?"name"\s*:\s*"([^"]+)"')
        if ($toolMatches.Count -eq 0 -and $line -match '"type"\s*:\s*"tool_use"') {
            $nameMatches = [regex]::Matches($line, '"name"\s*:\s*"([^"]+)"')
            foreach ($nm in $nameMatches) {
                $n = $nm.Groups[1].Value
                $toolCount++
                $lastKind = 'tool'
                $lastToolName = $n
                $lastIsToolUse = $true
                $assistantTextOnlyTail = 0
                $sawAssistant = $true
                if ($n -eq $prevTool) { $consecutiveSameTool++ } else { $consecutiveSameTool = 1; $prevTool = $n }
                if ($consecutiveSameTool -gt $maxSameTool) { $maxSameTool = $consecutiveSameTool }
                if ($n -match '^(Write|StrReplace|Shell|Delete|EditNotebook|CallMcpTool)$') { $mutating++ }
                elseif ($n -match '^(Read|Grep|SemanticSearch|Glob)$') { $readOnly++ }
            }
            continue
        }
        if ($toolMatches.Count -gt 0) {
            foreach ($tm in $toolMatches) {
                $n = $tm.Groups[1].Value
                $toolCount++
                $lastKind = 'tool'
                $lastToolName = $n
                $lastIsToolUse = $true
                $assistantTextOnlyTail = 0
                $sawAssistant = $true
                if ($n -eq $prevTool) { $consecutiveSameTool++ } else { $consecutiveSameTool = 1; $prevTool = $n }
                if ($consecutiveSameTool -gt $maxSameTool) { $maxSameTool = $consecutiveSameTool }
                if ($n -match '^(Write|StrReplace|Shell|Delete|EditNotebook|CallMcpTool)$') { $mutating++ }
                elseif ($n -match '^(Read|Grep|SemanticSearch|Glob)$') { $readOnly++ }
            }
            continue
        }

        if ($line -match '"role"\s*:\s*"assistant"') {
            $sawAssistant = $true
            $lastIsToolUse = $false
            if ($line -match '"type"\s*:\s*"text"') {
                $lastKind = 'thought'
                $assistantTextOnlyTail++
            }
            else {
                $lastKind = 'assistant'
            }
        }
        elseif ($line -match '"role"\s*:\s*"user"') {
            $lastKind = 'user'
            $lastIsToolUse = $false
        }
    }

    $looksComplete = $false
    $last = $lines[$lines.Count - 1]
    if ($turnSuccess -or ($turnEnded -and $last -match '"type"\s*:\s*"turn_ended"')) {
        $looksComplete = $true
    }
    elseif ($last -match '"role"\s*:\s*"assistant"' -and $last -notmatch '"type"\s*:\s*"tool_use"') {
        if ($last -match '(?i)(\*\*Stopped\*\*|DONE checklist|final_summary|Shipped|completed_subtitle)') {
            $looksComplete = $true
        }
    }

    $ageMinutes = [math]::Round(((Get-Date) - $item.LastWriteTime).TotalMinutes, 1)
    $startedAge = $ageMinutes
    try {
        $startedAge = [math]::Round(((Get-Date) - $item.CreationTime).TotalMinutes, 1)
    }
    catch { }

    $progressUnchangedMin = $null
    $prior = $null
    if ($PriorProgress -and $PriorProgress.ContainsKey($Path)) {
        $prior = $PriorProgress[$Path]
    }
    if ($prior) {
        $priorTools = 0
        $since = $null
        if ($prior -is [hashtable] -or $prior -is [System.Collections.IDictionary]) {
            $priorTools = [int]$prior['tool_count']
            $since = [string]$prior['progress_unchanged_since']
        }
        else {
            $priorTools = [int]$prior.tool_count
            $since = [string]$prior.progress_unchanged_since
        }
        if ($priorTools -eq $toolCount -and $since) {
            try {
                $sinceDt = [datetime]::Parse($since, $null, [System.Globalization.DateTimeStyles]::RoundtripKind)
                $progressUnchangedMin = [math]::Round(((Get-Date) - $sinceDt).TotalMinutes, 1)
            }
            catch { $progressUnchangedMin = $null }
        }
    }

    return [pscustomobject]@{
        FullName               = $item.FullName
        LastWriteTime          = $item.LastWriteTime
        AgeMinutes             = $ageMinutes
        StartedAgeMinutes      = $startedAge
        ByteLength             = [int64]$item.Length
        LineCount              = $lines.Count
        ToolCount              = $toolCount
        MutatingTools          = $mutating
        ReadOnlyTools          = $readOnly
        LastKind               = $lastKind
        LastToolName           = $lastToolName
        LastIsToolUse          = [bool]$lastIsToolUse
        TurnEnded              = [bool]$turnEnded
        TurnEndedSuccess       = [bool]$turnSuccess
        Aborted                = [bool]$aborted
        LooksComplete          = [bool]$looksComplete
        MaxSameToolRun         = $maxSameTool
        TextOnlyAssistantTail  = $assistantTextOnlyTail
        SawAssistant           = [bool]$sawAssistant
        ProgressUnchangedMin   = $progressUnchangedMin
        LastLinePreview        = if ($last.Length -gt 160) { $last.Substring(0, 160) + '...' } else { $last }
    }
}

function Get-LeaseMap {
    $map = @{}
    if (-not (Test-Path -LiteralPath $leaseDir)) { return $map }
    Get-ChildItem -LiteralPath $leaseDir -Filter '*.json' -File -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $obj = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            $id = [string]$obj.agent_id
            if (-not $id) { $id = $_.BaseName }
            $age = $null
            if ($obj.last_event_at) {
                try {
                    $dt = [datetime]::Parse([string]$obj.last_event_at, $null, [System.Globalization.DateTimeStyles]::RoundtripKind)
                    $age = [math]::Round(((Get-Date).ToUniversalTime() - $dt.ToUniversalTime()).TotalMinutes, 1)
                }
                catch { $age = $null }
            }
            $map[$id] = [pscustomobject]@{
                agent_id      = $id
                last_event    = [string]$obj.last_event
                last_kind     = [string]$obj.last_kind
                last_tool     = [string]$obj.last_tool
                last_event_at = [string]$obj.last_event_at
                age_min       = $age
                step_idx      = [int]$obj.step_idx
                progress_idx  = [int]$obj.progress_idx
                thought_idx   = [int]$obj.thought_idx
                tool_count    = [int]$obj.tool_count
                ended         = [bool]$obj.ended
                parent        = [string]$obj.parent_conversation_id
            }
        }
        catch { }
    }
    return $map
}

function Get-HungHelpers {
    param([hashtable]$PriorSample)

    $now = Get-Date
    $current = @{}
    $hung = New-Object System.Collections.Generic.List[object]

    $procs = @(Get-Process -Name 'Cursor','node' -ErrorAction SilentlyContinue)
    foreach ($p in $procs) {
        $cpu = 0.0
        if ($p.CPU) { $cpu = [double]$p.CPU }
        $ws = [int64]$p.WorkingSet64
        $current["$($p.Id)"] = [pscustomobject]@{
            pid        = $p.Id
            name       = $p.ProcessName
            cpu        = $cpu
            ws_mb      = [math]::Round($ws / 1MB, 1)
            sampled_at = $now.ToString('o')
        }
    }

    $anyRecentTranscript = $false
    if (Test-Path -LiteralPath $TranscriptRoot) {
        $cut = (Get-Date).AddMinutes(-2)
        $hit = Get-ChildItem -LiteralPath $TranscriptRoot -Recurse -Filter '*.jsonl' -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -gt $cut } |
            Select-Object -First 1
        if ($hit) { $anyRecentTranscript = $true }
    }

    if ($PriorSample -and -not $anyRecentTranscript) {
        foreach ($key in $current.Keys) {
            $cur = $current[$key]
            if (-not $PriorSample.ContainsKey($key)) { continue }
            $old = $PriorSample[$key]
            $oldCpu = 0.0
            $oldAt = $null
            if ($old -is [hashtable] -or $old -is [System.Collections.IDictionary]) {
                $oldCpu = [double]$old['cpu']
                $oldAt = [string]$old['sampled_at']
            }
            else {
                $oldCpu = [double]$old.cpu
                $oldAt = [string]$old.sampled_at
            }
            $elapsed = $null
            if ($oldAt) {
                try {
                    $odt = [datetime]::Parse($oldAt, $null, [System.Globalization.DateTimeStyles]::RoundtripKind)
                    $elapsed = ((Get-Date) - $odt).TotalMinutes
                }
                catch { $elapsed = $null }
            }
            $delta = $cur.cpu - $oldCpu
            if ($elapsed -and $elapsed -ge $IdleMinutes -and $delta -lt 0.15 -and $cur.ws_mb -ge 80 -and $cur.name -match '^(Cursor|node)$') {
                $cmd = ''
                try {
                    $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$($cur.pid)" -ErrorAction SilentlyContinue
                    if ($cim) { $cmd = [string]$cim.CommandLine }
                }
                catch { }
                $isMainUi = $cmd -and ($cmd -notmatch '--type=')
                if ($isMainUi) { continue }
                $snippet = $cmd
                if ($snippet.Length -gt 140) { $snippet = $snippet.Substring(0, 140) + '...' }
                [void]$hung.Add([pscustomobject]@{
                        pid     = $cur.pid
                        name    = $cur.name
                        ws_mb   = $cur.ws_mb
                        cpu_delta = [math]::Round($delta, 3)
                        elapsed_min = [math]::Round($elapsed, 1)
                        command = $snippet
                    })
            }
        }
    }

    return [pscustomobject]@{ Current = $current; Hung = $hung }
}

if (-not (Test-Path -LiteralPath $TranscriptRoot)) {
    $failMd = @"
# Stuck agent local watcher report

Generated: $((Get-Date).ToString('o'))
Scan root: ``$TranscriptRoot``
**ERROR:** transcript root missing. Exit 2.
"@
    Set-Content -LiteralPath $reportPath -Value $failMd -Encoding UTF8
    Set-Content -LiteralPath $signalPath -Value $failMd -Encoding UTF8
    Write-Error "Transcript root not found: $TranscriptRoot"
    exit 2
}

$now = Get-Date
$notified = Get-JsonMap $notifiedPath
$priorProgress = Get-JsonMap $progressPath
$priorProc = Get-JsonMap $procSamplePath
$leases = Get-LeaseMap
$nextProgress = @{}
$scannedParents = 0
$scannedSubs = 0
$stuck = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]
$coldAborted = New-Object System.Collections.Generic.List[object]
$uiGhosts = New-Object System.Collections.Generic.List[object]
$ghostMaxAgeMin = $GhostWindowHours * 60

function Add-StuckRow {
    param($Id, $Parent, $Age, $Reasons, $Tools, $LastKind, $LeaseNote)
    if (Test-NeverInterrupt $Id) { return }
    $action = 'Parent MUST Task-interrupt once (AUTO) with stop-planning text; if no deliverable, abandon ID and finish slice in parent or one AUTO replacement'
    if ($notified.ContainsKey($Id)) {
        $action = 'Already queued once this incident - parent should abandon if still idle; do not interrupt again'
    }
    [void]$stuck.Add([pscustomobject]@{
            agent_id           = $Id
            parent_path        = $Parent
            last_write_age_min = $Age
            stuck_reason       = ($Reasons -join ',')
            action             = $action
            tool_count         = $Tools
            last_kind          = $LastKind
            lease              = $LeaseNote
        })
}

Get-ChildItem -LiteralPath $TranscriptRoot -Directory -ErrorAction Stop | ForEach-Object {
    $parentId = $_.Name
    $parentJsonl = Join-Path $_.FullName "$parentId.jsonl"
    if (Test-Path -LiteralPath $parentJsonl) { $scannedParents++ }

    $subDir = Join-Path $_.FullName 'subagents'
    if (-not (Test-Path -LiteralPath $subDir)) { return }

    Get-ChildItem -LiteralPath $subDir -Filter '*.jsonl' -File | ForEach-Object {
        $scannedSubs++
        $id = $_.BaseName
        $info = Get-TranscriptSignals -Path $_.FullName -PriorProgress $priorProgress
        if (-not $info) { return }

        $unchangedSince = $now.ToString('o')
        $prior = $null
        if ($priorProgress.ContainsKey($info.FullName)) { $prior = $priorProgress[$info.FullName] }
        if ($prior) {
            $priorTools = 0
            $priorSince = $null
            if ($prior -is [hashtable] -or $prior -is [System.Collections.IDictionary]) {
                $priorTools = [int]$prior['tool_count']
                $priorSince = [string]$prior['progress_unchanged_since']
            }
            else {
                $priorTools = [int]$prior.tool_count
                $priorSince = [string]$prior.progress_unchanged_since
            }
            if ($priorTools -eq $info.ToolCount -and $priorSince) {
                $unchangedSince = $priorSince
            }
        }

        $nextProgress[$info.FullName] = [pscustomobject]@{
            size                     = $info.ByteLength
            mtime                    = $info.LastWriteTime.ToString('o')
            agent_id                 = $id
            parent                   = $parentId
            tool_count               = $info.ToolCount
            line_count               = $info.LineCount
            last_kind                = $info.LastKind
            progress_unchanged_since = $unchangedSince
            scanned_at               = $now.ToString('o')
        }

        $lease = $null
        foreach ($lk in $leases.Keys) {
            if ($id.StartsWith($lk, [System.StringComparison]::OrdinalIgnoreCase) -or $lk.StartsWith($id.Substring(0, [Math]::Min(8, $id.Length)), [System.StringComparison]::OrdinalIgnoreCase)) {
                $lease = $leases[$lk]
                break
            }
        }

        if ($info.TurnEndedSuccess -or ($info.LooksComplete -and $info.TurnEnded -and -not $info.Aborted)) {
            if ($info.AgeMinutes -le $ghostMaxAgeMin) {
                [void]$uiGhosts.Add([pscustomobject]@{
                        agent_id           = $id
                        parent_path        = $parentId
                        last_write_age_min = $info.AgeMinutes
                        note               = 'completed on disk (turn_ended/success); Multitask UI may still show Running - do not interrupt; abandon in UI if still listed'
                    })
            }
            return
        }

        if ($info.Aborted -and $info.TurnEnded -and -not $info.TurnEndedSuccess) {
            [void]$coldAborted.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    stuck_reason       = 'already_aborted_cold'
                    action             = 'UI may still show Planning; transcript already aborted - do not re-interrupt; abandon / finish in parent'
                })
            return
        }

        $clockAge = $info.StartedAgeMinutes
        if ($info.AgeMinutes -gt $clockAge) { $clockAge = $info.AgeMinutes }

        if ($clockAge -gt $LiveStuckMaxAgeMinutes -and -not $info.TurnEnded -and -not $info.LooksComplete) {
            [void]$coldAborted.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    stuck_reason       = 'cold_missing_turn_ended'
                    action             = 'Too old for live interrupt; abandon if UI still lists it; do not resume'
                })
            return
        }

        $reasons = New-Object System.Collections.Generic.List[string]
        $leaseNote = ''
        if ($lease) {
            $leaseNote = "lease kind=$($lease.last_kind) progress=$($lease.progress_idx) thought=$($lease.thought_idx) age=$($lease.age_min)"
            if ($lease.ended) { $leaseNote += ' ended=true' }
        }

        # Ghost via lease end + transcript complete already returned. Lease-ended without turn_ended is still a candidate.

        $isLive = $false

        # 1) Planning stall: started, 0 tools, age > planning window (prompt-only forever).
        if (-not $info.TurnEndedSuccess -and -not $info.LooksComplete -and $info.ToolCount -eq 0 -and $clockAge -ge $PlanningStallMinutes -and $clockAge -le $LiveStuckMaxAgeMinutes) {
            $isLive = $true
            [void]$reasons.Add('planning_stall_zero_tools')
            if (-not $info.SawAssistant) { [void]$reasons.Add('prompt_only_no_assistant') }
        }

        # 2) Tool-starvation: last kind is thought/user/assistant, tools stale across ticks or last write is thought-only.
        if (-not $isLive -and -not $info.TurnEndedSuccess -and -not $info.LooksComplete -and $clockAge -le $LiveStuckMaxAgeMinutes) {
            $starved = $false
            if ($info.LastKind -eq 'thought' -and $info.AgeMinutes -ge $IdleMinutes) { $starved = $true }
            if ($info.ProgressUnchangedMin -and $info.ProgressUnchangedMin -ge $IdleMinutes -and $info.ToolCount -ge 0 -and -not $info.TurnEnded) { $starved = $true }
            if ($lease -and $lease.last_kind -eq 'thought' -and $lease.age_min -ge $IdleMinutes -and $lease.progress_idx -eq $info.ToolCount) { $starved = $true }
            if ($starved -and $info.ToolCount -gt 0) {
                $isLive = $true
                [void]$reasons.Add('tool_starvation_thinking_only')
            }
            elseif ($starved -and $info.ToolCount -eq 0 -and $clockAge -ge $PlanningStallMinutes) {
                $isLive = $true
                if ($reasons -notcontains 'planning_stall_zero_tools') { [void]$reasons.Add('planning_stall_zero_tools') }
            }
        }

        # 3) Stuck-tool (ClawGuard): last event is tool_use, no result.
        # Require two-tick progress freeze OR a stale preToolUse lease so a
        # live worker whose jsonl has not flushed yet is not flagged on tick 1.
        $stuckToolConfirmed = $false
        if ($info.ProgressUnchangedMin -and $info.ProgressUnchangedMin -ge $IdleMinutes) { $stuckToolConfirmed = $true }
        if ($lease -and $lease.last_event -eq 'preToolUse' -and $lease.age_min -ge $IdleMinutes -and -not $lease.ended) { $stuckToolConfirmed = $true }
        if (-not $info.TurnEndedSuccess -and -not $info.LooksComplete -and $clockAge -le $LiveStuckMaxAgeMinutes -and $stuckToolConfirmed) {
            if ($info.LastIsToolUse) {
                $isLive = $true
                [void]$reasons.Add('stuck_tool_pending')
            }
        }

        # 4) Read/Grep loop — two-tick freeze + live window (not 20-day-old files).
        if (-not $info.TurnEndedSuccess -and $clockAge -le $LiveStuckMaxAgeMinutes -and $info.ReadOnlyTools -ge 2 -and $info.MutatingTools -eq 0) {
            if ($info.ProgressUnchangedMin -and $info.ProgressUnchangedMin -ge $IdleMinutes) {
                $isLive = $true
                [void]$reasons.Add('read_grep_loop')
            }
        }

        # 5) Same-tool loop (ClawGuard loop) — live window only.
        if (-not $info.TurnEndedSuccess -and $clockAge -le $LiveStuckMaxAgeMinutes -and $info.MaxSameToolRun -ge 6) {
            if ($info.ProgressUnchangedMin -and $info.ProgressUnchangedMin -ge $IdleMinutes) {
                $isLive = $true
                [void]$reasons.Add('repeated_tool_loop')
            }
        }

        if ($isLive) {
            Add-StuckRow -Id $id -Parent $parentId -Age $info.AgeMinutes -Reasons $reasons -Tools $info.ToolCount -LastKind $info.LastKind -LeaseNote $leaseNote
        }
        elseif ($info.AgeMinutes -lt $IdleMinutes -and -not $info.TurnEnded -and -not $info.LooksComplete) {
            [void]$skipped.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    tool_count         = $info.ToolCount
                    last_kind          = $info.LastKind
                    note               = 'under idle / planning-stall window; still watched'
                })
        }
    }
}

# Leases with no matching transcript (child never wrote jsonl).
foreach ($lk in $leases.Keys) {
    $lease = $leases[$lk]
    if ($lease.ended) { continue }
    $already = $false
    $leasePrefix = $lk
    if ($leasePrefix.Length -gt 8) { $leasePrefix = $leasePrefix.Substring(0, 8) }
    foreach ($row in $stuck) {
        if ($row.agent_id -eq $lk) { $already = $true; break }
        if ($leasePrefix.Length -ge 8 -and $row.agent_id.StartsWith($leasePrefix, [System.StringComparison]::OrdinalIgnoreCase)) { $already = $true; break }
    }
    if ($already) { continue }
    if (Test-NeverInterrupt $lk) { continue }
    $age = $lease.age_min
    if (-not $age) { continue }
    if ($lease.progress_idx -eq 0 -and $age -ge $PlanningStallMinutes -and $age -le $LiveStuckMaxAgeMinutes) {
        $parent = $lease.parent
        if (-not $parent) { $parent = 'lease-only' }
        Add-StuckRow -Id $lk -Parent $parent -Age $age -Reasons @('planning_stall_lease_no_tools') -Tools 0 -LastKind $lease.last_kind -LeaseNote "lease-only $($lease.last_event)"
    }
}

Save-JsonMap $nextProgress $progressPath

$procResult = Get-HungHelpers -PriorSample $priorProc
Save-JsonMap $procResult.Current $procSamplePath
$hung = $procResult.Hung

$EmitInterruptRequests = -not $NoEmitInterruptRequests
$newInterruptCount = 0
$newStuckIds = New-Object System.Collections.Generic.List[string]
if ($EmitInterruptRequests) {
    foreach ($row in $stuck) {
        if ($notified.ContainsKey($row.agent_id)) { continue }
        if (Test-NeverInterrupt $row.agent_id) { continue }
        $newInterruptCount++
        $newStuckIds.Add($row.agent_id) | Out-Null
        $file = Join-Path $queueDir ("{0}__{1}.md" -f $row.parent_path, $row.agent_id)
        $body = @"
# Stuck agent interrupt request (local watcher)

Generated: $($now.ToString('o'))
Parent chat: ``$($row.parent_path)``
Stuck subagent: ``$($row.agent_id)``
Idle / age minutes: $($row.last_write_age_min)
Reason: $($row.stuck_reason)
Last event kind: $($row.last_kind)
Tool count: $($row.tool_count)
Lease: $($row.lease)

## Parent action (required)

This watcher **queues only** — it does **not** spawn Cursor agents and does **not** Task-interrupt.
The owning Multitask parent must interrupt:

1. Read ``$signalPath`` (PARENT-SIGNAL.md) at the start of the next parent turn.
2. In parent chat ``$($row.parent_path)``, call ``Task`` with ``resume: $($row.agent_id)``, ``interrupt: true``, omit model (AUTO only).
3. Prompt body (exact):

``````
$stopPlanning
``````

4. If the child still does not deliver: abandon ``$($row.agent_id)`` - do not interrupt again. Finish the same slice in the parent, or spawn at most ONE AUTO replacement with "no planning - edit or answer immediately".
5. Report one line: Child $($row.agent_id) stuck -> interrupted -> abandoned; finishing in parent (or one AUTO replacement).

## Limits
- AUTO only; no Opus / Max / thinking-high pins
- No explore fan-out while any sibling is stuck
- One interrupt per ID per incident
- Do not interrupt IDs that already have turn_ended/success (UI ghosts)
- Do not interrupt never-interrupt prefixes: $($NeverInterruptPrefixes -join ', ')
"@
        Set-Content -LiteralPath $file -Value $body -Encoding UTF8
        $notified[$row.agent_id] = [pscustomobject]@{
            parent     = $row.parent_path
            queued_at  = $now.ToString('o')
            reason     = $row.stuck_reason
            queue_file = $file
        }
    }
    Save-JsonMap $notified $notifiedPath
}

$stuckIds = @($stuck | ForEach-Object { $_.agent_id })
$toRemove = @()
foreach ($key in @($notified.Keys)) {
    if ($stuckIds -notcontains $key) { $toRemove += $key }
}
foreach ($k in $toRemove) { $notified.Remove($k) | Out-Null }
if ($toRemove.Count -gt 0) {
    Save-JsonMap $notified $notifiedPath
    foreach ($k in $toRemove) {
        Get-ChildItem -LiteralPath $queueDir -Filter "*__$k.md" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

# PARENT-SIGNAL.md — short, parent-first, no window.
$sig = New-Object System.Text.StringBuilder
[void]$sig.AppendLine('# Parent signal - read this first')
[void]$sig.AppendLine('')
[void]$sig.AppendLine("Generated: $($now.ToString('o'))")
[void]$sig.AppendLine("Live stuck (interrupt): $($stuck.Count)")
[void]$sig.AppendLine("New interrupt requests: $newInterruptCount")
[void]$sig.AppendLine("Hung helper processes: $($hung.Count)")
[void]$sig.AppendLine("UI ghosts (do not interrupt): $($uiGhosts.Count)")
[void]$sig.AppendLine('')
[void]$sig.AppendLine('## Interrupt now')
[void]$sig.AppendLine('')
if ($stuck.Count -eq 0) {
    [void]$sig.AppendLine('_None._ Watcher is complement only; still status-check children yourself.')
}
else {
    foreach ($r in $stuck) {
        [void]$sig.AppendLine("- ``$($r.agent_id)`` parent=``$($r.parent_path)`` reason=``$($r.stuck_reason)`` tools=$($r.tool_count) kind=$($r.last_kind)")
    }
    [void]$sig.AppendLine('')
    [void]$sig.AppendLine('Consume: Task resume=<id> interrupt=true (AUTO). Prompt = stop-planning text in interrupt-queue markdown.')
}
[void]$sig.AppendLine('')
[void]$sig.AppendLine("Queue dir: ``$queueDir``")
[void]$sig.AppendLine("Full report: ``$reportPath``")
$signalText = $sig.ToString()
[System.IO.File]::WriteAllText($signalPath, $signalText, (New-Object System.Text.UTF8Encoding $false))

$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine('# Stuck agent local watcher report')
[void]$md.AppendLine('')
[void]$md.AppendLine("Generated: $($now.ToString('o'))")
[void]$md.AppendLine("Scan root: ``$TranscriptRoot``")
[void]$md.AppendLine("Signals: transcript last-kind + hook lease + cross-tick tool_count + helper CPU (not mtime-only)")
[void]$md.AppendLine("Planning stall: $PlanningStallMinutes min / tool-starvation & stuck-tool: $IdleMinutes min")
[void]$md.AppendLine("Ghost window: last $GhostWindowHours hour(s)")
[void]$md.AppendLine("Parents scanned: $scannedParents / Subagents scanned: $scannedSubs / Leases: $($leases.Count)")
[void]$md.AppendLine("Live stuck: $($stuck.Count) / New interrupt requests: $newInterruptCount / Hung helpers: $($hung.Count) / Cold: $($coldAborted.Count) / UI ghosts: $($uiGhosts.Count)")
[void]$md.AppendLine('')
[void]$md.AppendLine('## Strategies (sourced)')
[void]$md.AppendLine('')
[void]$md.AppendLine('1. Dead-man lease + isolated supervisor -- Crontap/Healthchecks.io dead-man, OpenClaw isolated heartbeat, Antigravity step_idx. Cursor hooks write leases/*.json; this task reads them. Thought-only does not increment progress.')
[void]$md.AppendLine('2. Stuck-tool / tool-starvation / zero-tool planning stall -- ClawGuard stuck-tool + loop. Last jsonl event kind beats file mtime. Prompt-only forever (0 tools, age > planning window) is live-stuck even when the file never contains "planning next moves".')
[void]$md.AppendLine('3. Hung helper CPU -- OpenClaw process-isolation: sample Cursor/node CPU across ticks; 0-CPU helpers are reported, never auto-interrupted.')
[void]$md.AppendLine('')
[void]$md.AppendLine('## Live stuck')
[void]$md.AppendLine('')
[void]$md.AppendLine('True stalls only (no ``turn_ended``/success). Watcher queues interrupt markdown; owning Multitask parent must ``Task`` interrupt. Read ``PARENT-SIGNAL.md`` first.')
[void]$md.AppendLine('')
if ($stuck.Count -eq 0) {
    [void]$md.AppendLine('_None._')
}
else {
    [void]$md.AppendLine('| agent_id | parent_path | age (min) | tools | last kind | stuck reason | action |')
    [void]$md.AppendLine('| --- | --- | ---: | ---: | --- | --- | --- |')
    foreach ($r in $stuck) {
        [void]$md.AppendLine("| ``$($r.agent_id)`` | ``$($r.parent_path)`` | $($r.last_write_age_min) | $($r.tool_count) | $($r.last_kind) | $($r.stuck_reason) | $($r.action) |")
    }
}
[void]$md.AppendLine('')
[void]$md.AppendLine('## Hung helper processes')
[void]$md.AppendLine('')
[void]$md.AppendLine('PID + name only. Do **not** kill these from the watcher. Investigate if transcripts are also silent.')
[void]$md.AppendLine('')
if ($hung.Count -eq 0) {
    [void]$md.AppendLine('_None this tick (or a transcript wrote in the last 2 minutes, so helpers are assumed busy)._')
}
else {
    [void]$md.AppendLine('| pid | name | ws_mb | cpu_delta | elapsed_min | command |')
    [void]$md.AppendLine('| ---: | --- | ---: | ---: | ---: | --- |')
    foreach ($h in $hung) {
        [void]$md.AppendLine("| $($h.pid) | $($h.name) | $($h.ws_mb) | $($h.cpu_delta) | $($h.elapsed_min) | $($h.command) |")
    }
}
[void]$md.AppendLine('')
[void]$md.AppendLine('## Completed but UI may ghost')
[void]$md.AppendLine('')
[void]$md.AppendLine('These have ``turn_ended``/success on disk. **Do not interrupt**. Abandon in the UI if still listed.')
[void]$md.AppendLine('')
if ($uiGhosts.Count -eq 0) {
    [void]$md.AppendLine('_None in ghost window._')
}
else {
    [void]$md.AppendLine('| agent_id | parent_path | age (min) | note |')
    [void]$md.AppendLine('| --- | --- | ---: | --- |')
    foreach ($r in ($uiGhosts | Sort-Object last_write_age_min | Select-Object -First 40)) {
        [void]$md.AppendLine("| ``$($r.agent_id)`` | ``$($r.parent_path)`` | $($r.last_write_age_min) | $($r.note) |")
    }
}
[void]$md.AppendLine('')
[void]$md.AppendLine('## Cold aborted (do not re-interrupt)')
[void]$md.AppendLine('')
if ($coldAborted.Count -eq 0) {
    [void]$md.AppendLine('_None._')
}
else {
    [void]$md.AppendLine('| agent_id | parent_path | age (min) | note |')
    [void]$md.AppendLine('| --- | --- | ---: | --- |')
    foreach ($r in ($coldAborted | Sort-Object last_write_age_min -Descending | Select-Object -First 25)) {
        [void]$md.AppendLine("| ``$($r.agent_id)`` | ``$($r.parent_path)`` | $($r.last_write_age_min) | $($r.action) |")
    }
}
[void]$md.AppendLine('')
[void]$md.AppendLine('## How a parent consumes the queue')
[void]$md.AppendLine('')
[void]$md.AppendLine('1. Open ``PARENT-SIGNAL.md`` (this folder). If Live stuck is 0, you are done with the watcher for this turn — still do your own child status-check.')
[void]$md.AppendLine('2. For each **Interrupt now** id: ``Task`` ``resume: <id>`` ``interrupt: true`` (AUTO). Use the stop-planning prompt in ``interrupt-queue\<parent>__<id>.md``.')
[void]$md.AppendLine('3. One interrupt per id. If it does not deliver, abandon. Never interrupt ghosts or the never-interrupt prefix list.')
[void]$md.AppendLine('4. Slack fires only when a **new** live-stuck id is queued — not on every tick, not for ghosts.')
[void]$md.AppendLine('')
[void]$md.AppendLine('Watcher is complement, not substitute. Parent duty in ``stuck-agent-supervisor.mdc`` still binds.')
[void]$md.AppendLine('')
[void]$md.AppendLine("Interrupt queue: ``$queueDir``")

$reportText = $md.ToString()
[System.IO.File]::WriteAllText($reportPath, $reportText, (New-Object System.Text.UTF8Encoding $false))

$payload = [pscustomobject]@{
    generated_at             = $now.ToString('o')
    detector                 = 'multi-signal-v2'
    transcript_root          = $TranscriptRoot
    planning_stall_minutes   = $PlanningStallMinutes
    idle_minutes             = $IdleMinutes
    scanned_parents          = $scannedParents
    scanned_subagents        = $scannedSubs
    lease_count              = $leases.Count
    live_stuck               = [object[]]@($stuck.ToArray())
    new_interrupt_requests   = $newInterruptCount
    hung_helpers             = [object[]]@($hung.ToArray())
    cold_aborted             = [object[]]@($coldAborted.ToArray())
    ui_ghosts_completed      = [object[]]@($uiGhosts.ToArray())
    actively_working         = [object[]]@($skipped.ToArray())
    interrupt_queue_dir      = $queueDir
    parent_signal_path       = $signalPath
    parent_must_interrupt    = $true
    watcher_spawns_agents    = $false
}
[System.IO.File]::WriteAllText($jsonPath, ($payload | ConvertTo-Json -Depth 8), (New-Object System.Text.UTF8Encoding $false))
[System.IO.File]::WriteAllText($statusPath, ($payload | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding $false))

if ($newInterruptCount -gt 0 -and -not $NoSlack -and (Test-Path -LiteralPath $slackScript)) {
    $idList = ($newStuckIds -join ', ')
    $text = "Stuck-watcher NEW live-stuck ($newInterruptCount): $idList. Read PARENT-SIGNAL.md and interrupt-queue (parent owns Task-interrupt). Ghosts not paged."
    try {
        $null = & powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $slackScript -To Phil -Text $text
    }
    catch { }
}

if ([Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost') {
    $hasConsole = $false
    try { $null = [Console]::WindowHeight; $hasConsole = $true } catch { $hasConsole = $false }
    if ($hasConsole) {
        Write-Host $reportText
        Write-Host "Report written: $reportPath"
        Write-Host "Parent signal: $signalPath"
    }
}

if ($stuck.Count -gt 0) { exit 1 }
exit 0
