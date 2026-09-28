# PSScriptAnalyzer settings for every AIC PowerShell script.
#
# Canonical copy. Point the analyzer at this file rather than relying on
# analyzer defaults, so the gate does not drift between machines:
#
#   Invoke-ScriptAnalyzer -Path .\script.ps1 `
#       -Settings c:\analog-pim\core-assets\scripts\lint\PSScriptAnalyzerSettings.psd1
#
# Severity: Error and Warning are the gate. Information is advisory.
#
# One rule is excluded on purpose. Every exclusion needs a reason on the
# line above it; an unexplained exclusion is rule-suppression debt.

@{
    Severity = @('Error', 'Warning')

    ExcludeRules = @(
        # PSAvoidUsingWriteHost conflicts with a house hard rule.
        # no-ansi-vt100-windows-shells.mdc requires operator-facing colored
        # status in classic Windows consoles to use the native console API
        # (`Write-Host -ForegroundColor`) precisely because ANSI and VT100
        # escape sequences do not render in Windows PowerShell 5.1 or
        # cmd.exe. The analyzer's blanket objection to Write-Host assumes a
        # pipeline-output context that operator status lines are not.
        #
        # This does NOT license Write-Host for data. Data still goes to
        # Write-Output, and diagnostics still go to Write-Verbose, per the
        # authoring practices in ascii-syntax-and-powershell-first-run.mdc.
        'PSAvoidUsingWriteHost'
    )

    Rules = @{
        # Windows PowerShell 5.1 is the floor on operator hosts, so flag
        # syntax that only parses on PowerShell 7+.
        PSUseCompatibleSyntax = @{
            Enable         = $true
            TargetVersions = @('5.1', '7.4')
        }
    }
}
