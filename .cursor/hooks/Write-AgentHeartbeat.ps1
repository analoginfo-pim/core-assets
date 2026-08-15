#Requires -Version 5.1
<#
.SYNOPSIS
  Cursor hook: renew a per-agent dead-man lease. Fail-open, no console, no deny.

.DESCRIPTION
  Isolated supervisor pattern (OpenClaw / Healthchecks.io dead-man / Antigravity
  step_idx). Thought-only events bump thought_idx, not progress_idx.
  Never blocks the agent (always allow). Never pops a window.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$leaseRoot = 'C:\analog-pim\.cursor\automations\local-watcher-state\leases'

function Write-AllowAndExit {
    param([int]$Code = 0)
    try {
        [Console]::Out.WriteLine('{"permission":"allow"}')
    }
    catch { }
    exit $Code
}

try {
    $raw = [Console]::In.ReadToEnd()
}
catch {
    Write-AllowAndExit
}

if ([string]::IsNullOrWhiteSpace($raw)) {
    Write-AllowAndExit
}

try {
    $evt = $raw | ConvertFrom-Json
}
catch {
    Write-AllowAndExit
}

$eventName = [string]$evt.hook_event_name
if (-not $eventName) { $eventName = 'unknown' }

$toolName = [string]$evt.tool_name
$subId = [string]$evt.subagent_id
$convId = [string]$evt.conversation_id
$genId = [string]$evt.generation_id
$parentConv = [string]$evt.parent_conversation_id
$transcript = [string]$evt.transcript_path
if (-not $transcript) { $transcript = [string]$evt.agent_transcript_path }

$agentId = $subId
if ([string]::IsNullOrWhiteSpace($agentId)) { $agentId = $convId }
if ([string]::IsNullOrWhiteSpace($agentId)) { $agentId = $genId }
if ([string]::IsNullOrWhiteSpace($agentId)) { Write-AllowAndExit }

$isEnd = $eventName -match '^(stop|sessionEnd|subagentStop)$'
$isTool = $eventName -match '^(preToolUse|postToolUse|postToolUseFailure|beforeShellExecution|afterShellExecution|beforeMCPExecution|afterMCPExecution|beforeReadFile|afterFileEdit)$'
$isThought = $eventName -match '^(afterAgentThought|afterAgentResponse)$'
$isStart = $eventName -match '^(sessionStart|subagentStart|beforeSubmitPrompt)$'

$kind = 'other'
if ($isEnd) { $kind = 'end' }
elseif ($isTool) { $kind = 'tool' }
elseif ($isThought) { $kind = 'thought' }
elseif ($isStart) { $kind = 'start' }

try {
    if (-not (Test-Path -LiteralPath $leaseRoot)) {
        New-Item -ItemType Directory -Force -Path $leaseRoot | Out-Null
    }

    $safeId = ($agentId -replace '[^A-Za-z0-9._-]', '_')
    $path = Join-Path $leaseRoot ($safeId + '.json')
    $now = (Get-Date).ToUniversalTime().ToString('o')

    $prev = $null
    if (Test-Path -LiteralPath $path) {
        try { $prev = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $prev = $null }
    }

    $step = 1
    $progress = 0
    $thoughts = 0
    $tools = 0
    if ($prev) {
        if ($prev.step_idx) { $step = [int]$prev.step_idx + 1 } else { $step = 1 }
        if ($prev.progress_idx) { $progress = [int]$prev.progress_idx }
        if ($prev.thought_idx) { $thoughts = [int]$prev.thought_idx }
        if ($prev.tool_count) { $tools = [int]$prev.tool_count }
    }

    if ($isTool) {
        $progress++
        $tools++
    }
    if ($isThought) { $thoughts++ }

    $obj = [ordered]@{
        agent_id               = $agentId
        parent_conversation_id = $parentConv
        conversation_id        = $convId
        generation_id          = $genId
        last_event             = $eventName
        last_kind              = $kind
        last_tool              = $toolName
        last_event_at          = $now
        step_idx               = $step
        progress_idx           = $progress
        thought_idx            = $thoughts
        tool_count             = $tools
        ended                  = [bool]$isEnd
        end_status             = if ($isEnd) { [string]$evt.status } else { $null }
        transcript_path        = $transcript
        hook_pid               = $PID
    }

    $tmp = $path + '.tmp.' + $PID
    $json = ($obj | ConvertTo-Json -Compress)
    [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding $false))
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    }
    Rename-Item -LiteralPath $tmp -NewName (Split-Path -Leaf $path) -Force
}
catch {
    # Fail-open: lease write must never block the agent.
}

Write-AllowAndExit
