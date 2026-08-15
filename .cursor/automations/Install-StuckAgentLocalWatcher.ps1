<#
.SYNOPSIS
  Install or uninstall the local Stuck-agent watcher Scheduled Task (Hidden).

.DESCRIPTION
  Registers AIC-StuckAgentLocalWatcher to run Scan-StuckAgents.ps1 every
  N minutes under the current user with a Hidden PowerShell host so the
  scan never steals focus (launch-consoles-minimized / host-session-safety).

  Cursor Automations Cloud Agents cannot see local transcript paths — this
  local Hidden task is the Enable path that works on the workstation.

.PARAMETER IntervalMinutes
  How often to scan (default 5).

.PARAMETER Uninstall
  Remove the Scheduled Task instead of creating it.

.PARAMETER RunOnceNow
  After install, run one scan immediately via Start-Process -WindowStyle Hidden.
#>
[CmdletBinding()]
param(
    [ValidateRange(1, 60)]
    [int]$IntervalMinutes = 5,
    [switch]$Uninstall,
    [switch]$RunOnceNow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$taskName = 'AIC-StuckAgentLocalWatcher'
$scriptPath = Join-Path $PSScriptRoot 'Scan-StuckAgents.ps1'

if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing scanner script: $scriptPath"
}

function Invoke-HiddenScan {
    param([string]$PowerShellExe, [string]$ScanScript)
    # Never Normal/Maximized; never Activate/BringToFront.
    $args = @(
        '-WindowStyle', 'Hidden',
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $ScanScript
    )
    $p = Start-Process -FilePath $PowerShellExe -ArgumentList $args `
        -WindowStyle Hidden -Wait -PassThru
    return [int]$p.ExitCode
}

if ($Uninstall) {
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Output "Removed Scheduled Task: $taskName"
    }
    else {
        Write-Output "No Scheduled Task named $taskName was registered."
    }
    exit 0
}

# Prefer Windows PowerShell for Scheduled Task (stable -WindowStyle Hidden).
$pwshExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $pwshExe)) {
    $cmd = Get-Command powershell -ErrorAction Stop
    $pwshExe = $cmd.Source
}

# Hidden console: WindowStyle Hidden on both the task action argv and Start-Process.
$arg = "-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
$action = New-ScheduledTaskAction -Execute $pwshExe -Argument $arg

# Task Scheduler rejects TimeSpan.MaxValue; use ~10 years of repetition.
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -Hidden

# Interactive logon so the task can read the user's Cursor transcript tree
# without storing a password. Window is still Hidden via -WindowStyle.
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'Local AIC stuck-agent supervisor (Hidden). Scans Cursor agent-transcripts on this machine; writes latest-report.md and queues interrupt requests for Multitask parents. Does not spawn Cursor agents. Replaces non-functional Cloud Automation path.' `
    -Force | Out-Null

Write-Output "Registered Scheduled Task: $taskName"
Write-Output "  Interval: every $IntervalMinutes minute(s)"
Write-Output "  Script:   $scriptPath"
Write-Output "  Host:     $pwshExe -WindowStyle Hidden"
Write-Output "  Hidden:   yes (task settings Hidden + WindowStyle Hidden)"
Write-Output "  User:     $env:USERNAME (Interactive, no focus steal)"
Write-Output ''
Write-Output "Verify:  Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State"
Write-Output "Reports: $($PSScriptRoot)\local-watcher-state\latest-report.md"
Write-Output "Queue:   $($PSScriptRoot)\local-watcher-state\interrupt-queue\"

if ($RunOnceNow) {
    Write-Output ''
    Write-Output 'Running one Hidden scan now (no console window)...'
    $code = Invoke-HiddenScan -PowerShellExe $pwshExe -ScanScript $scriptPath
    Write-Output "Scan exit code: $code (0=none stuck, 1=stuck found, 2=path missing)"
    exit $code
}

exit 0
