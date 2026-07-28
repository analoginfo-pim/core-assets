<#
.SYNOPSIS
  Local stuck-agent scanner for AIC PIM Cursor transcripts (Windows host).

.DESCRIPTION
  Scans agent-transcripts (parents + */subagents/*.jsonl) on THIS machine.
  Writes a latest report and per-parent interrupt request files the Multitask
  parent can act on. Does NOT call Cursor Cloud Agents and does NOT assume a
  remote VM can see C:\Users\phil\... paths.

  This is the reliable complement to the optional Cursor Automation named
  "Stuck agent supervisor", which runs as a Cloud Agent and cannot see local
  transcript paths - so it cannot unstick planning stalls on this workstation.

.PARAMETER IdleMinutes
  Minimum minutes since last transcript write before a subagent can be flagged
  as stuck (default 15).

.PARAMETER TranscriptRoot
  Override scan root (default: Phil's c-analog-pim agent-transcripts).

.PARAMETER StateDir
  Where reports / interrupt queue / already-notified state live.

.PARAMETER EmitInterruptRequests
  When set (default), write interrupt-request markdown files for each newly
  stuck ID (once per incident until cleared).
#>
[CmdletBinding()]
param(
    [double]$IdleMinutes = 15,
    # Beyond this age, missing turn_ended is treated as cold/abandoned UI ghost, not live stuck.
    [double]$LiveStuckMaxAgeMinutes = 240,
    [string]$TranscriptRoot = 'C:\Users\phil\.cursor\projects\c-analog-pim\agent-transcripts',
    [string]$StateDir = '',
    [switch]$NoEmitInterruptRequests,
    [switch]$IncludeAbortedCold = $false
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

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
New-Item -ItemType Directory -Force -Path $queueDir | Out-Null

$stopPlanning = @'
STOP PLANNING. Deliver NOW from what you already know.
Return a short DONE checklist (done / deferred / blocked) for THIS slice only.
No more exploration, no more Read/Grep loops, no more planning.
If you lack facts, mark blocked with the one smallest missing path - then stop.
'@

function Get-NotifiedMap {
    if (-not (Test-Path -LiteralPath $notifiedPath)) {
        return @{}
    }
    try {
        $raw = Get-Content -LiteralPath $notifiedPath -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($raw)) { return @{} }
        $obj = $raw | ConvertFrom-Json
        $map = @{}
        foreach ($p in $obj.PSObject.Properties) {
            $map[$p.Name] = $p.Value
        }
        return $map
    }
    catch {
        Write-Warning "Could not parse notified-ids.json; starting fresh. $_"
        return @{}
    }
}

function Save-NotifiedMap([hashtable]$Map) {
    $obj = [ordered]@{}
    foreach ($key in @($Map.Keys)) {
        $val = $Map[$key]
        if ($val -is [pscustomobject]) {
            $obj[$key] = $val
        }
        else {
            $obj[$key] = $val
        }
    }
    $json = ($obj | ConvertTo-Json -Depth 6)
    [System.IO.File]::WriteAllText($notifiedPath, $json, (New-Object System.Text.UTF8Encoding $false))
}

function Get-TranscriptTailInfo {
    param([string]$Path, [int]$TailLines = 40)

    $item = Get-Item -LiteralPath $Path
    $lines = @(Get-Content -LiteralPath $Path -ErrorAction Stop)
    if ($lines.Count -eq 0) {
        return $null
    }

    $start = [Math]::Max(0, $lines.Count - $TailLines)
    $tail = $lines[$start..($lines.Count - 1)]
    $tailText = $tail -join "`n"
    $sampleStart = [Math]::Max(0, $lines.Count - 300)
    $sample = ($lines[$sampleStart..($lines.Count - 1)]) -join "`n"
    $last = $lines[-1]

    $turnEndedAny = $sample -match '"type"\s*:\s*"turn_ended"'
    $turnEndedSuccess = $sample -match '"type"\s*:\s*"turn_ended"[^\n]*"status"\s*:\s*"success"'
    $aborted = $sample -match '"status"\s*:\s*"aborted"'
    $toolUse = ([regex]::Matches($sample, '"type"\s*:\s*"tool_use"')).Count
    $planningTail = $tailText -match '(?i)planning next moves'
    $readOnlyTail = ($tailText -match '"name"\s*:\s*"(Read|Grep|SemanticSearch|Glob)"') -and `
        ($tailText -notmatch '"name"\s*:\s*"(Write|StrReplace|Shell|Delete|EditNotebook)"')
    $endsMidTool = $last -match '"type"\s*:\s*"tool_use"|\"name\"\s*:\s*\"(Read|Grep|Shell)'
    $endsTurn = $last -match '"type"\s*:\s*"turn_ended"'
    $looksComplete = $false
    if ($last -match '"role"\s*:\s*"assistant"' -and $last -notmatch '"type"\s*:\s*"tool_use"') {
        if ($last -match '(?i)(\*\*Stopped\*\*|DONE checklist|final_summary|Shipped|completed_subtitle|Child .+ stuck)') {
            $looksComplete = $true
        }
        # Substantial final assistant prose without a pending tool_use usually means the turn finished
        # even when the runtime omitted turn_ended (common on older transcripts).
        if ($last.Length -gt 400 -and $last -match '"type"\s*:\s*"text"') {
            $looksComplete = $true
        }
    }

    return [pscustomobject]@{
        FullName          = $item.FullName
        LastWriteTime     = $item.LastWriteTime
        AgeMinutes        = [math]::Round(((Get-Date) - $item.LastWriteTime).TotalMinutes, 1)
        LineCount         = $lines.Count
        TurnEndedAny      = [bool]$turnEndedAny
        TurnEndedSuccess  = [bool]$turnEndedSuccess
        Aborted           = [bool]$aborted
        ToolUseCount      = $toolUse
        PlanningInTail    = [bool]$planningTail
        ReadOnlyTail      = [bool]$readOnlyTail
        EndsMidTool       = [bool]$endsMidTool
        EndsTurnEnded     = [bool]$endsTurn
        LooksComplete     = [bool]$looksComplete
        LastLinePreview   = if ($last.Length -gt 180) { $last.Substring(0, 180) + '...' } else { $last }
    }
}

if (-not (Test-Path -LiteralPath $TranscriptRoot)) {
    $msg = "Transcript root not found: $TranscriptRoot (Cloud Agents will always hit this on a remote VM.)"
    Write-Error $msg
    exit 2
}

$now = Get-Date
$notified = Get-NotifiedMap
$scannedParents = 0
$scannedSubs = 0
$stuck = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]
$coldAborted = New-Object System.Collections.Generic.List[object]

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
        $info = Get-TranscriptTailInfo -Path $_.FullName
        if (-not $info) { return }

        $reasons = New-Object System.Collections.Generic.List[string]
        $isLiveStuck = $false
        $inLiveWindow = ($info.AgeMinutes -ge $IdleMinutes) -and ($info.AgeMinutes -le $LiveStuckMaxAgeMinutes)

        if ($info.Aborted -and $info.EndsTurnEnded -and -not $info.TurnEndedSuccess) {
            $coldAborted.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    stuck_reason       = 'already_aborted_cold'
                    action             = 'UI may still show Planning; transcript already aborted - do not re-interrupt; abandon / finish in parent'
                }) | Out-Null
        }
        elseif ($info.AgeMinutes -gt $LiveStuckMaxAgeMinutes -and -not $info.TurnEndedAny -and -not $info.LooksComplete) {
            $coldAborted.Add([pscustomobject]@{
                    agent_id           = $id
                    parent_path        = $parentId
                    last_write_age_min = $info.AgeMinutes
                    stuck_reason       = 'cold_missing_turn_ended'
                    action             = 'Too old for live interrupt; abandon if UI still lists it; do not resume'
                }) | Out-Null
        }

        if ($inLiveWindow -and -not $info.LooksComplete -and -not $info.TurnEndedSuccess) {
            if (-not $info.TurnEndedAny) {
                $isLiveStuck = $true
                $reasons.Add('no_turn_ended')
            }
            if ($info.PlanningInTail -and -not $info.EndsTurnEnded) {
                $isLiveStuck = $true
                $reasons.Add('planning_in_tail')
            }
            if ($info.EndsMidTool -and -not $info.EndsTurnEnded) {
                $isLiveStuck = $true
                $reasons.Add('ended_mid_tool_call')
            }
            if ($info.ReadOnlyTail -and -not $info.TurnEndedAny) {
                $isLiveStuck = $true
                $reasons.Add('read_grep_only_tail')
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
"@
        Set-Content -LiteralPath $file -Value $body -Encoding UTF8
        $notified[$row.agent_id] = [pscustomobject]@{
            parent     = $row.parent_path
            queued_at  = $now.ToString('o')
            reason     = $row.stuck_reason
            queue_file = $file
        }
    }
    Save-NotifiedMap $notified
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
    Save-NotifiedMap $notified
    foreach ($k in $toRemove) {
        Get-ChildItem -LiteralPath $queueDir -Filter "*__$k.md" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

# (report uses $stuck and $coldAborted directly)

$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine("# Stuck agent local watcher report")
[void]$md.AppendLine("")
[void]$md.AppendLine("Generated: $($now.ToString('o'))")
[void]$md.AppendLine("Scan root: ``$TranscriptRoot``")
[void]$md.AppendLine("Idle threshold: $IdleMinutes minutes")
[void]$md.AppendLine("Parents scanned: $scannedParents / Subagents scanned: $scannedSubs")
[void]$md.AppendLine("Live stuck: $($stuck.Count) / New interrupt requests: $newInterruptCount / Cold aborted (not live): $($coldAborted.Count)")
[void]$md.AppendLine("")
[void]$md.AppendLine("## Live stuck")
[void]$md.AppendLine("")
if ($stuck.Count -eq 0) {
    [void]$md.AppendLine("_None._")
}
else {
    [void]$md.AppendLine("| agent_id | parent_path | last write age (min) | stuck reason | action |")
    [void]$md.AppendLine("| --- | --- | ---: | --- | --- |")
    foreach ($r in $stuck) {
        [void]$md.AppendLine("| ``$($r.agent_id)`` | ``$($r.parent_path)`` | $($r.last_write_age_min) | $($r.stuck_reason) | $($r.action) |")
    }
}
[void]$md.AppendLine("")
[void]$md.AppendLine("## Cold aborted (UI ghosts - do not re-interrupt)")
[void]$md.AppendLine("")
if ($coldAborted.Count -eq 0) {
    [void]$md.AppendLine("_None in this scan window (only flagged when idle and aborted)._")
}
else {
    [void]$md.AppendLine("| agent_id | parent_path | age (min) | note |")
    [void]$md.AppendLine("| --- | --- | ---: | --- |")
    foreach ($r in ($coldAborted | Sort-Object last_write_age_min -Descending | Select-Object -First 25)) {
        [void]$md.AppendLine("| ``$($r.agent_id)`` | ``$($r.parent_path)`` | $($r.last_write_age_min) | $($r.action) |")
    }
}
[void]$md.AppendLine("")
[void]$md.AppendLine("## Architecture note")
[void]$md.AppendLine("")
[void]$md.AppendLine("Cursor Automations cron runs as a Cloud Agent on a remote VM. That host does not have C:\Users\phil\.cursor\projects\... . A Cloud-only supervisor cannot see or interrupt local Multitask children. Use this local watcher + parent duty instead.")
[void]$md.AppendLine("")
[void]$md.AppendLine("Interrupt queue: ``$queueDir``")

$md.ToString() | Set-Content -LiteralPath $reportPath -Encoding UTF8

$payload = [pscustomobject]@{
    generated_at           = $now.ToString('o')
    transcript_root        = $TranscriptRoot
    idle_minutes           = $IdleMinutes
    scanned_parents        = $scannedParents
    scanned_subagents      = $scannedSubs
    live_stuck             = [object[]]@($stuck.ToArray())
    new_interrupt_requests = $newInterruptCount
    cold_aborted           = [object[]]@($coldAborted.ToArray())
    actively_working       = [object[]]@($skipped.ToArray())
    interrupt_queue_dir    = $queueDir
}
$json = $payload | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($jsonPath, $json, (New-Object System.Text.UTF8Encoding $false))

Write-Host $md.ToString()
Write-Host "Report written: $reportPath"
Write-Host "JSON written:   $jsonPath"

if ($stuck.Count -gt 0) {
    exit 1
}
exit 0
