#Requires -Version 5.1
<#
.SYNOPSIS
  Refresh FireHOL / ET Open / AbuseIPDB list snapshots under core-assets/threat-intel.

.DESCRIPTION
  Writes firehol.list, et-open.list, abuseipdb.list under the per-feed directories.
  Full FireHOL/ET dumps are OK for AIC internal assets; AbuseIPDB needs an API
  key parameter or an export file. Respect upstream licenses (see threat-intel/README.md).

.PARAMETER ConfirmDownload
  Required for any internet download.

.PARAMETER DownloadFirehol
  Fetch FireHOL level1.netset.

.PARAMETER DownloadEtOpen
  Fetch Emerging Threats Open block IPs.

.PARAMETER DownloadAbuseIpdb
  Fetch AbuseIPDB blacklist (requires -AbuseIpdbApiKey).

.PARAMETER AbuseIpdbApiKey
  Operator-supplied API key (never read from process environment).

.PARAMETER AbuseIpdbExportFile
  Air-gapped AbuseIPDB export to convert into abuseipdb.list.

.PARAMETER SeedSamplesOnly
  Write RFC 5737 fixture subsets only (no network).

.EXAMPLE
  pwsh .\scripts\Update-ThreatIntelLists.ps1 -ConfirmDownload -DownloadFirehol -DownloadEtOpen
#>
[CmdletBinding()]
param(
    [switch]$ConfirmDownload,
    [switch]$DownloadFirehol,
    [switch]$DownloadEtOpen,
    [switch]$DownloadAbuseIpdb,
    [string]$AbuseIpdbApiKey = '',
    [string]$AbuseIpdbExportFile = '',
    [switch]$SeedSamplesOnly
)

$ErrorActionPreference = 'Stop'

function Convert-ToIpCidrLines {
    param([Parameter(Mandatory)][string]$Raw)
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($Raw -split "`r?`n")) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        if ($t -match '^(?i)ipAddress') { continue }
        $candidate = ($t -split ',')[0].Trim().Trim('"')
        if ($candidate -match '^\d{1,3}(\.\d{1,3}){3}(/\d{1,2})?$' -or
            $candidate -match '^[0-9a-fA-F:]+(/\d{1,3})?$') {
            [void]$out.Add($candidate)
        }
    }
    return ($out -join "`n")
}

function Write-ListFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content,
        [Parameter(Mandatory)][string]$Header
    )
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $body = if ($Content.Trim().StartsWith('#')) {
        $Content.TrimEnd() + "`n"
    } else {
        "$Header`n$($Content.TrimEnd())`n"
    }
    Set-Content -LiteralPath $Path -Value $body -Encoding utf8
}

try {
    $selfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = (Resolve-Path (Join-Path $selfDir '..')).Path
    $tiRoot = Join-Path $repoRoot 'threat-intel'
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')

    $sampleFirehol = @"
# Sample FireHOL-style entries (RFC 5737 TEST-NET-1). Replace with licensed dump.
192.0.2.0/24
198.51.100.99
"@
    $sampleEt = @"
# Sample Emerging Threats Open-style entries (RFC 5737 TEST-NET-2).
198.51.100.0/24
"@
    $sampleAbuse = @"
# Sample AbuseIPDB offline-export style entries (RFC 5737 TEST-NET-3).
203.0.113.0/24
203.0.113.50
"@

    $wantDownload = $DownloadFirehol -or $DownloadEtOpen -or $DownloadAbuseIpdb
    if ($wantDownload -and -not $ConfirmDownload) {
        Write-Error 'Update-ThreatIntelLists.ps1: internet downloads require -ConfirmDownload'
        exit 2
    }

    if ($SeedSamplesOnly -or (-not $wantDownload -and -not $AbuseIpdbExportFile)) {
        Write-ListFile -Path (Join-Path $tiRoot 'firehol\firehol.list') -Content $sampleFirehol `
            -Header "# FireHOL fixture $stamp"
        Write-ListFile -Path (Join-Path $tiRoot 'et-open\et-open.list') -Content $sampleEt `
            -Header "# ET Open fixture $stamp"
        Write-ListFile -Path (Join-Path $tiRoot 'abuseipdb\abuseipdb.list') -Content $sampleAbuse `
            -Header "# AbuseIPDB fixture $stamp"
        Write-Host "Wrote sample lists under $tiRoot"
        if (-not $wantDownload -and -not $AbuseIpdbExportFile) { exit 0 }
    }

    if ($DownloadFirehol) {
        $url = 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset'
        Write-Host "Downloading FireHOL level1 from $url ..."
        $raw = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 180
        $converted = Convert-ToIpCidrLines -Raw $raw.Content
        if (-not $converted) {
            Write-Error 'Update-ThreatIntelLists.ps1: FireHOL download produced no IP/CIDR lines'
            exit 2
        }
        Write-ListFile -Path (Join-Path $tiRoot 'firehol\firehol.list') -Content $converted `
            -Header "# FireHOL level1.netset import $stamp - respect FireHOL / source licenses"
        Write-Host ("Wrote firehol.list ({0} entries)" -f (($converted -split "`n").Count))
    }

    if ($DownloadEtOpen) {
        $url = 'https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt'
        Write-Host "Downloading ET Open block IPs from $url ..."
        $raw = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 180
        $converted = Convert-ToIpCidrLines -Raw $raw.Content
        if (-not $converted) {
            Write-Error 'Update-ThreatIntelLists.ps1: ET Open download produced no IP/CIDR lines'
            exit 2
        }
        Write-ListFile -Path (Join-Path $tiRoot 'et-open\et-open.list') -Content $converted `
            -Header "# Emerging Threats Open-style import $stamp - follow Proofpoint / ET licensing"
        Write-Host ("Wrote et-open.list ({0} entries)" -f (($converted -split "`n").Count))
    }

    if ($AbuseIpdbExportFile) {
        if (-not (Test-Path -LiteralPath $AbuseIpdbExportFile)) {
            Write-Error "Update-ThreatIntelLists.ps1: AbuseIPDB export not found: $AbuseIpdbExportFile"
            exit 2
        }
        $raw = Get-Content -LiteralPath $AbuseIpdbExportFile -Raw
        $converted = Convert-ToIpCidrLines -Raw $raw
        Write-ListFile -Path (Join-Path $tiRoot 'abuseipdb\abuseipdb.list') -Content $converted `
            -Header "# AbuseIPDB offline export import $stamp - comply with AbuseIPDB ToS"
        Write-Host 'Wrote abuseipdb.list from export file'
    } elseif ($DownloadAbuseIpdb) {
        if (-not $AbuseIpdbApiKey) {
            Write-Error 'Update-ThreatIntelLists.ps1: -DownloadAbuseIpdb requires -AbuseIpdbApiKey (never env)'
            exit 2
        }
        $apiUrl = 'https://api.abuseipdb.com/api/v2/blacklist?confidenceMinimum=90&limit=10000'
        Write-Host 'Downloading AbuseIPDB blacklist (confidenceMinimum=90) ...'
        $headers = @{ Key = $AbuseIpdbApiKey; Accept = 'text/plain' }
        $raw = Invoke-WebRequest -Uri $apiUrl -Headers $headers -UseBasicParsing -TimeoutSec 180
        $converted = Convert-ToIpCidrLines -Raw $raw.Content
        if (-not $converted) {
            Write-Error 'Update-ThreatIntelLists.ps1: AbuseIPDB download produced no IP lines'
            exit 2
        }
        Write-ListFile -Path (Join-Path $tiRoot 'abuseipdb\abuseipdb.list') -Content $converted `
            -Header "# AbuseIPDB API blacklist import $stamp - comply with AbuseIPDB ToS"
        Write-Host ("Wrote abuseipdb.list ({0} entries)" -f (($converted -split "`n").Count))
    } elseif (-not (Test-Path -LiteralPath (Join-Path $tiRoot 'abuseipdb\abuseipdb.list'))) {
        Write-ListFile -Path (Join-Path $tiRoot 'abuseipdb\abuseipdb.list') -Content $sampleAbuse `
            -Header "# AbuseIPDB fixture $stamp (no API key; replace via -DownloadAbuseIpdb or export)"
        Write-Host 'Wrote AbuseIPDB fixture (no API download)'
    }

    Write-Host "Done. Run sync-to-projects.ps1 to push lists into pim-offline-server / pim-installers."
    exit 0
} catch {
    $script = Split-Path -Leaf $PSCommandPath
    Write-Error "${script}: threat-intel update failed: $_"
    exit 2
}
