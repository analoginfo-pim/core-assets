<#
.SYNOPSIS
  Local stuck-agent scanner for AIC PIM Cursor transcripts (Windows host).

.DESCRIPTION
  Scans agent-transcripts (parents + */subagents/*.jsonl) on THIS machine.
  Writes latest-report.md / .json and queues one interrupt-request markdown
  per newly stuck ID. Does NOT spawn Cursor agents and does NOT rely on
  Cloud Automations (Cloud Agents cannot see C:\Users\phil\... paths).

  Live stuck = true stalls only (no turn_ended/success). UI-ghost completed
  agents (turn_ended/success while Multitask may still show Running) are
  listed separately — never interrupt-queued.

.PARAMETER IdleMinutes
  Minutes of idle / no useful progress before a subagent is live-stuck
  (default 4; rule band ~3-5).

.PARAMETER LiveStuckMaxAgeMinutes
  Beyond this age, missing turn_ended is cold/abandoned, not live stuck.

.PARAMETER GhostWindowHours
  How far back to list completed-but-UI-may-ghost IDs (default 6).

.PARAMETER TranscriptRoot
  Override scan root (default: Phil's c-analog-pim agent-transcripts).
#>
[CmdletBinding()]
param(
    [double]$IdleMinutes = 4,
    [double]$LiveStuckMaxAgeMinutes = 240,
    [double]$GhostWindowHours = 6,
    [string]$TranscriptRoot = 'C:\Users\phil\.cursor\projects\c-analog-pim\agent-transcripts',
    [string]$StateDir = '',
    [switch]$NoEmitInterruptRequests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $StateDir) {
    $StateDir = Join-Path $PSScriptRoot 'local-watcher-state'
}

$queueDir = Join-Path $StateDir 'interrupt-queue'
$reportPath = Join-Path $StateDir 'latest-report.md'
$jsonPath = Join-Path $StateDir 'latest-report.json'
$notifiedPath = Join-Path $StateDir 'notified-ids.json'
$growthPath = Join-Path $StateDir 'growth-state.json'

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
New-Item -ItemType Directory -Force -Path $queueDir | Out-Null

$stopPlanning = @'
STOP PLANNING. Deliver NOW from what you already know.
Return a short DONE checklist (done / deferred / blocked) for THIS slice only.
No more exploration, no more Read/Grep loops, no more planning.
If you lack facts, mark blocked with the one smallest missing path - then stop.
'@

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

function Get-TranscriptTailInfo {
    param(
        [string]$Path,
        [int]$TailLines = 50,
        [hashtable]$PriorGrowth
    )

    $item = Get-Item -LiteralPath $Path
    # Prefer StreamReader for large jsonl; fall back to Get-Content.
    $lines = [System.Collections.Generic.List[string]]::new()
    try {
        $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $sr = New-Object System.IO.StreamReader($fs)
            try {
                while ($null -ne ($line = $sr.ReadLine())) {
                    $lines.Add($line)
                }
            }
            finally { $sr.Dispose() }
        }
        finally { $fs.Dispose() }
    }
    catch {
        $lines = [System.Collections.Generic.List[string]]::new()
        foreach ($l in @(Get-Content -LiteralPath $Path -ErrorAction Stop)) {
            $lines.Add($l)
        }
    }

    if ($lines.Count -eq 0) { return $null }

    $start = [Math]::Max(0, $lines.Count - $TailLines)
    $tail = $lines.GetRange($start, $lines.Count - $start)
    $tailText = ($tail -join "`n")
    $sampleStart = [Math]::Max(0, $lines.Count - 400)
    $sample = ($lines.GetRange($sampleStart, $lines.Count - $sampleStart) -join "`n")
    $last = $lines[$lines.Count - 1]

    $turnEndedAny = $sample -match '"type"\s*:\s*"turn_ended"'
    $turnEndedSuccess = $sample -match '"type"\s*:\s*"turn_ended"[^\n]*"status"\s*:\s*"success"'
    $aborted = $sample -match '"status"\s*:\s*"aborted"'
    $toolUse = ([regex]::Matches($sample, '"type"\s*:\s*"tool_use"')).Count
    $mutatingTools = ([regex]::Matches($tailText, '"name"\s*:\s*"(Write|StrReplace|Shell|Delete|EditNotebook|CallMcpTool)"')).Count
    $readTools = ([regex]::Matches($tailText, '"name"\s*:\s*"(Read|Grep|SemanticSearch|Glob)"')).Count
    $planningTail = $tailText -match '(?i)planning next moves'
    $readOnlyTail = ($readTools -ge 2) -and ($mutatingTools -eq 0)
    $endsMidTool = $last -match '"type"\s*:\s*"tool_use"'
    $endsTurn = $last -match '"type"\s*:\s*"turn_ended"'
    $toolUseInTail = ([regex]::Matches($tailText, '"type"\s*:\s*"tool_use"')).Count
    $planningNoTools = $planningTail -and ($toolUseInTail -eq 0)

    $looksComplete = $false
    if ($turnEndedSuccess -or $endsTurn) {
        $looksComplete = $true
    }
    elseif ($last -match '"role"\s*:\s*"assistant"' -and $last -notmatch '"type"\s*:\s*"tool_use"') {
        if ($last -match '(?i)(\*\*Stopped\*\*|DONE checklist|final_summary|Shipped|completed_subtitle|Child .+ stuck)') {
            $looksComplete = $true
        }
        if ($last.Length -gt 400 -and $last -match '"type"\s*:\s*"text"') {
            $looksComplete = $true
        }
    }

    $ageMinutes = [math]::Round(((Get-Date) - $item.LastWriteTime).TotalMinutes, 1)
    $size = [int64]$item.Length
    $noGrowth = $false
    $prior = $null
    if ($PriorGrowth -and $PriorGrowth.ContainsKey($Path)) {
        $prior = $PriorGrowth[$Path]
    }
    if ($prior) {
        $priorSize = 0
        $priorMtime = $null
        if ($prior -is [hashtable] -or $prior -is [System.Collections.IDictionary]) {
            $priorSize = [int64]$prior['size']
            $priorMtime = [string]$prior['mtime']
        }
        else {
            $priorSize = [int64]$prior.size
            $priorMtime = [string]$prior.mtime
        }
        $mtimeUnchanged = ($priorMtime -eq $item.LastWriteTime.ToString('o'))
        if (($priorSize -eq $size) -and $mtimeUnchanged -and ($ageMinutes -ge $script:IdleMinutes)) {
            $noGrowth = $true
        }
    }

    return [pscustomobject]@{
        FullName           = $item.FullName
        LastWriteTime      = $item.LastWriteTime
        AgeMinutes         = $ageMinutes
        ByteLength         = $size
        LineCount          = $lines.Count
        TurnEndedAny       = [bool]$turnEndedAny
        TurnEndedSuccess   = [bool]$turnEndedSuccess
        Aborted            = [bool]$aborted
        ToolUseCount       = $toolUse
        ToolUseInTail      = $toolUseInTail
        PlanningInTail     = [bool]$planningTail
        PlanningNoTools    = [bool]$planningNoTools
        ReadOnlyTail       = [bool]$readOnlyTail
        EndsMidTool        = [bool]$endsMidTool
        EndsTurnEnded      = [bool]$endsTurn
        LooksComplete      = [bool]$looksComplete
        NoTranscriptGrowth = [bool]$noGrowth
        LastLinePreview    = if ($last.Length -gt 180) { $last.Substring(0, 180) + '...' } else { $last }
    }
}

if (-not (Test-Path -LiteralPath $TranscriptRoot)) {
    $msg = "Transcript root not found: $TranscriptRoot (Cloud Agents will always hit this on a remote VM.)"
    # Always leave a report so operators see the failure.
    $failMd = @"
# Stuck agent local watcher report

Generated: $((Get-Date).ToString('o'))
Scan root: ``$TranscriptRoot``
**ERROR:** transcript root missing. Exit 2.
"@
    Set-Content -LiteralPath $reportPath -Value $failMd -Encoding UTF8
    Write-Error $msg
    exit 2
}

$now = Get-Date
$notified = Get-JsonMap $notifiedPath
$priorGrowth = Get-JsonMap $growthPath
$nextGrowth = @{}
$scannedParents = 0
$scannedSubs = 0
$stuck = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]
$coldAborted = New-Object System.Collections.Generic.List[object]
$uiGhosts = New-Object System.Collections.Generic.List[object]
$ghostMaxAgeMin = $GhostWindowHours * 60

Get-ChildItem -LiteralPath $TranscriptRoot -Directory -ErrorAction Stop | ForEach-Object {
    $parentId = $_.Name
    $parentJsonl = Join-Path $_.FullName "$parentId.jsonl"
    if (Test-Path -LiteralPath $parentJsonl) {
        $scannedParents++
    }

    $subDir = Join-Path $_.FullName 'subagents'
    if (-not (Test-Path -LiteralPath $subDir)) { return }

    Get-ChildItem -LiteralPath $subDir -Filter '*.jsonl' -File | ForEach-Object {
        $scannedSubs++
        $id = $_.BaseName
        $info = Get-TranscriptTailInfo -Path $_.FullName -PriorGrowth $priorGrowth
        if (-not $info) { return }

        $nextGrowth[$info.FullName] = [pscustomobject]@{
            size       = $info.ByteLength
            mtime      = $info.LastWriteTime.ToString('o')
            agent_id   = $id
            parent     = $parentId
            scanned_at = $now.ToString('o')
        }

        # Completed on disk — never live-stuck; may still ghost in Multitask UI.
        if ($info.TurnEndedSuccess -or ($info.LooksComplete -and $info.TurnEndedAny -and -not $info.Aborted)) {
            if ($info.AgeMinutes -le $ghostMaxAgeMin) {
                $uiGhosts.Add([pscustomobject]@{
                        agent_id           = $id
                        parent_path        = $parentId
                        last_write_age_min = $info.AgeMinutes
                        note               = 'completed on disk (turn_ended/success); Multitask UI may still show Running - do not interrupt; abandon in UI if still listed'
                    }) | Out-Null
            }
            return
        }

        if ($info.Aborted -and $info.EndsTurnEnded -and -not $info.TurnEndedSuccess) {
            $coldAborted.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    stuck_reason       = 'already_aborted_cold'
                    action             = 'UI may still show Planning; transcript already aborted - do not re-interrupt; abandon / finish in parent'
                }) | Out-Null
            return
        }

        if ($info.AgeMinutes -gt $LiveStuckMaxAgeMinutes -and -not $info.TurnEndedAny -and -not $info.LooksComplete) {
            $coldAborted.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    stuck_reason       = 'cold_missing_turn_ended'
                    action             = 'Too old for live interrupt; abandon if UI still lists it; do not resume'
                }) | Out-Null
            return
        }

        # True live stuck: no successful turn_ended, inside live window.
        $inLiveWindow = ($info.AgeMinutes -ge $IdleMinutes) -and ($info.AgeMinutes -le $LiveStuckMaxAgeMinutes)
        $reasons = New-Object System.Collections.Generic.List[string]
        $isLiveStuck = $false

        if ($inLiveWindow -and -not $info.LooksComplete -and -not $info.TurnEndedSuccess -and -not $info.TurnEndedAny) {
            $isLiveStuck = $true
            $reasons.Add('no_turn_ended')

            if ($info.PlanningNoTools) {
                $reasons.Add('planning_no_tools')
            }
            elseif ($info.PlanningInTail) {
                $reasons.Add('planning_in_tail')
            }
            if ($info.ReadOnlyTail) {
                $reasons.Add('read_grep_loop')
            }
            if ($info.EndsMidTool) {
                $reasons.Add('ended_mid_tool_call')
            }
            if ($info.NoTranscriptGrowth) {
                $reasons.Add('no_transcript_growth')
            }
        }
        elseif ($inLiveWindow -and -not $info.LooksComplete -and -not $info.TurnEndedSuccess) {
            # Has some turn_ended noise but not success, or incomplete — still candidate if planning/read loop.
            if ($info.PlanningNoTools -or $info.ReadOnlyTail -or $info.NoTranscriptGrowth -or $info.EndsMidTool) {
                $isLiveStuck = $true
                if ($info.PlanningNoTools) { $reasons.Add('planning_no_tools') }
                if ($info.ReadOnlyTail) { $reasons.Add('read_grep_loop') }
                if ($info.NoTranscriptGrowth) { $reasons.Add('no_transcript_growth') }
                if ($info.EndsMidTool) { $reasons.Add('ended_mid_tool_call') }
                if (-not $info.TurnEndedAny) { $reasons.Add('no_turn_ended') }
            }
        }

        # Planning stall with no tools can be flagged slightly earlier (3 min) if still writing fluff.
        if (-not $isLiveStuck -and -not $info.TurnEndedSuccess -and -not $info.LooksComplete) {
            if ($info.PlanningNoTools -and ($info.AgeMinutes -ge [Math]::Min(3, $IdleMinutes)) -and ($info.AgeMinutes -le $LiveStuckMaxAgeMinutes)) {
                $isLiveStuck = $true
                $reasons.Add('planning_no_tools')
                if ($info.NoTranscriptGrowth) { $reasons.Add('no_transcript_growth') }
            }
        }

        if ($isLiveStuck) {
            $action = 'Parent MUST Task-interrupt once (AUTO) with stop-planning text; if no deliverable, abandon ID and finish slice in parent or one AUTO replacement'
            if ($notified.ContainsKey($id)) {
                $action = 'Already queued once this incident - parent should abandon if still idle; do not interrupt again'
            }
            $stuck.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    stuck_reason       = ($reasons -join ',')
                    action             = $action
                    last_write         = $info.LastWriteTime.ToString('o')
                    tool_use_sample    = $info.ToolUseCount
                }) | Out-Null
        }
        elseif ($info.AgeMinutes -lt $IdleMinutes -and -not $info.TurnEndedAny -and -not $info.LooksComplete) {
            $skipped.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    note               = 'actively writing / under idle threshold'
                }) | Out-Null
        }
    }
}

Save-JsonMap $nextGrowth $growthPath

$EmitInterruptRequests = -not $NoEmitInterruptRequests
$newInterruptCount = 0
if ($EmitInterruptRequests) {
    foreach ($row in $stuck) {
        if ($notified.ContainsKey($row.agent_id)) { continue }
        $newInterruptCount++
        $file = Join-Path $queueDir ("{0}__{1}.md" -f $row.parent_path, $row.agent_id)
        $body = @"
# Stuck agent interrupt request (local watcher)

Generated: $($now.ToString('o'))
Parent chat: ``$($row.parent_path)``
Stuck subagent: ``$($row.agent_id)``
Idle minutes: $($row.last_write_age_min)
Reason: $($row.stuck_reason)

## Parent action (required)

This watcher **queues only** — it does **not** spawn Cursor agents.
The owning Multitask parent must interrupt:

1. In parent chat ``$($row.parent_path)``, call ``Task`` with ``resume: $($row.agent_id)``, ``interrupt: true``, omit model (AUTO only).
2. Prompt body (exact):

``````
$stopPlanning
``````

3. If the child still does not deliver: abandon ``$($row.agent_id)`` - do not interrupt again. Finish the same slice in the parent, or spawn at most ONE AUTO replacement with "no planning - edit or answer immediately".
4. Report one line: Child $($row.agent_id) stuck -> interrupted -> abandoned; finishing in parent (or one AUTO replacement).

## Limits
- AUTO only; no Opus / Max / thinking-high pins
- No explore fan-out while any sibling is stuck
- One interrupt per ID per incident
- Do not interrupt IDs that already have turn_ended/success (UI ghosts)
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

# Prune notified entries that are no longer stuck (completed / gone)
$stuckIds = @($stuck | ForEach-Object { $_.agent_id })
$toRemove = @()
foreach ($key in @($notified.Keys)) {
    if ($stuckIds -notcontains $key) {
        $toRemove += $key
    }
}
foreach ($k in $toRemove) {
    $notified.Remove($k) | Out-Null
}
if ($toRemove.Count -gt 0) {
    Save-JsonMap $notified $notifiedPath
    foreach ($k in $toRemove) {
        Get-ChildItem -LiteralPath $queueDir -Filter "*__$k.md" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine('# Stuck agent local watcher report')
[void]$md.AppendLine('')
[void]$md.AppendLine("Generated: $($now.ToString('o'))")
[void]$md.AppendLine("Scan root: ``$TranscriptRoot``")
[void]$md.AppendLine("Idle threshold: $IdleMinutes minutes (rule band ~3-5)")
[void]$md.AppendLine("Ghost window: last $GhostWindowHours hour(s)")
[void]$md.AppendLine("Parents scanned: $scannedParents / Subagents scanned: $scannedSubs")
[void]$md.AppendLine("Live stuck: $($stuck.Count) / New interrupt requests: $newInterruptCount / Cold aborted: $($coldAborted.Count) / UI ghosts (completed): $($uiGhosts.Count)")
[void]$md.AppendLine('')
[void]$md.AppendLine('## Live stuck')
[void]$md.AppendLine('')
[void]$md.AppendLine('True stalls only (no ``turn_ended``/success). Watcher queues interrupt markdown; owning Multitask parent must ``Task`` interrupt.')
[void]$md.AppendLine('')
if ($stuck.Count -eq 0) {
    [void]$md.AppendLine('_None._')
}
else {
    [void]$md.AppendLine('| agent_id | parent_path | last write age (min) | stuck reason | action |')
    [void]$md.AppendLine('| --- | --- | ---: | --- | --- |')
    foreach ($r in $stuck) {
        [void]$md.AppendLine("| ``$($r.agent_id)`` | ``$($r.parent_path)`` | $($r.last_write_age_min) | $($r.stuck_reason) | $($r.action) |")
    }
}
[void]$md.AppendLine('')
[void]$md.AppendLine('## Completed but UI may ghost')
[void]$md.AppendLine('')
[void]$md.AppendLine('These have ``turn_ended``/success on disk. Multitask may still show Running/Planning - **do not interrupt**. Abandon in the UI if still listed.')
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
[void]$md.AppendLine('## Cold aborted (UI ghosts - do not re-interrupt)')
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
[void]$md.AppendLine('## Architecture note')
[void]$md.AppendLine('')
[void]$md.AppendLine('Cursor Automations cron runs as a Cloud Agent on a remote VM and **cannot** read ``C:\Users\phil\.cursor\projects\...``. Do not rely on Cloud for unstick. This local **Hidden** Scheduled Task + parent duty is the backup.')
[void]$md.AppendLine('')
[void]$md.AppendLine("Interrupt queue: ``$queueDir``")

$reportText = $md.ToString()
[System.IO.File]::WriteAllText($reportPath, $reportText, (New-Object System.Text.UTF8Encoding $false))

$payload = [pscustomobject]@{
    generated_at             = $now.ToString('o')
    transcript_root          = $TranscriptRoot
    idle_minutes             = $IdleMinutes
    ghost_window_hours       = $GhostWindowHours
    scanned_parents          = $scannedParents
    scanned_subagents        = $scannedSubs
    live_stuck               = [object[]]@($stuck.ToArray())
    new_interrupt_requests   = $newInterruptCount
    cold_aborted             = [object[]]@($coldAborted.ToArray())
    ui_ghosts_completed      = [object[]]@($uiGhosts.ToArray())
    actively_working         = [object[]]@($skipped.ToArray())
    interrupt_queue_dir      = $queueDir
    parent_must_interrupt    = $true
    watcher_spawns_agents    = $false
}
$json = $payload | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($jsonPath, $json, (New-Object System.Text.UTF8Encoding $false))

# File-only output when non-interactive / Hidden (avoid console noise).
if ([Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost') {
    $hasConsole = $false
    try {
        $null = [Console]::WindowHeight
        $hasConsole = $true
    }
    catch { $hasConsole = $false }
    if ($hasConsole) {
        Write-Host $reportText
        Write-Host "Report written: $reportPath"
    }
}

if ($stuck.Count -gt 0) {
    exit 1
}
exit 0
