<#
.SYNOPSIS
  Install or uninstall the local Stuck-agent watcher Scheduled Task.

.DESCRIPTION
  Registers AIC-StuckAgentLocalWatcher to run Scan-StuckAgents.ps1 every
  N minutes under the current interactive user. This is the Enable path that
  actually works on the workstation - Cursor Automations Cloud Agents cannot
  see local transcript paths.

.PARAMETER IntervalMinutes
  How often to scan (default 5). Use 5-15.

.PARAMETER Uninstall
  Remove the Scheduled Task instead of creating it.

.PARAMETER RunOnceNow
  After install, run one scan immediately.
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

if ($Uninstall) {
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Removed Scheduled Task: $taskName"
    }
    else {
        Write-Host "No Scheduled Task named $taskName was registered."
    }
    exit 0
}

$pwshCmd = Get-Command pwsh -ErrorAction SilentlyContinue
if ($pwshCmd) {
    $pwsh = $pwshCmd.Source
}
else {
    $pwsh = (Get-Command powershell -ErrorAction Stop).Source
}

$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
$action = New-ScheduledTaskAction -Execute $pwsh -Argument $arg
# Task Scheduler rejects TimeSpan.MaxValue; use ~10 years of repetition.
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'Local AIC stuck-agent supervisor: scan Cursor agent-transcripts on this machine and write interrupt requests for Multitask parents. Replaces Cloud Automation path that cannot see C:\Users\phil\... transcripts.' `
    -Force | Out-Null

Write-Host "Registered Scheduled Task: $taskName"
Write-Host "  Interval: every $IntervalMinutes minute(s)"
Write-Host "  Script:   $scriptPath"
Write-Host "  User:     $env:USERNAME (Interactive)"
Write-Host ""
Write-Host "Verify:  Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State"
Write-Host "Reports: $($PSScriptRoot)\local-watcher-state\latest-report.md"
Write-Host "Queue:   $($PSScriptRoot)\local-watcher-state\interrupt-queue\"

if ($RunOnceNow) {
    Write-Host ""
    Write-Host "Running one scan now..."
    & $pwsh -NoProfile -ExecutionPolicy Bypass -File $scriptPath
    $code = $LASTEXITCODE
    Write-Host "Scan exit code: $code (0=none stuck, 1=stuck found, 2=path missing)"
    exit $code
}

exit 0
