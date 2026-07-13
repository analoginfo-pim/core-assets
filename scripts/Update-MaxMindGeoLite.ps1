#Requires -Version 5.1
<#
.SYNOPSIS
  Download GeoLite2-Country.mmdb into core-assets/geoip using product constants.

.DESCRIPTION
  Reads account_id + license_key from geoip/maxmind-constants.toml (or
  -ConstantsFile). Writes GeoLite2-Country.mmdb next to the constants file.
  The .mmdb is gitignored (MaxMind redistribution terms); run this on the
  build/lab host before MSI packaging or sync when you need the binary seeded.

.PARAMETER ConstantsFile
  Path to maxmind-constants.toml. Default: ../geoip/maxmind-constants.toml

.PARAMETER DestinationDir
  Directory for the .mmdb. Default: same directory as ConstantsFile.

.EXAMPLE
  pwsh .\scripts\Update-MaxMindGeoLite.ps1
#>
[CmdletBinding()]
param(
    [string]$ConstantsFile = '',
    [string]$DestinationDir = ''
)

$ErrorActionPreference = 'Stop'
try {
    $selfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = (Resolve-Path (Join-Path $selfDir '..')).Path
    if (-not $ConstantsFile) {
        $ConstantsFile = Join-Path $repoRoot 'geoip\maxmind-constants.toml'
    }
    if (-not (Test-Path -LiteralPath $ConstantsFile)) {
        Write-Error "Update-MaxMindGeoLite.ps1: constants file not found: $ConstantsFile"
        exit 2
    }
    if (-not $DestinationDir) {
        $DestinationDir = Split-Path -Parent $ConstantsFile
    }
    if (-not (Test-Path -LiteralPath $DestinationDir)) {
        New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    }

    $accountId = $null
    $licenseKey = $null
    $edition = 'GeoLite2-Country'
    $downloadUrl = ''
    function Read-MaxMindToml([string]$path) {
        if (-not (Test-Path -LiteralPath $path)) { return }
        foreach ($line in Get-Content -LiteralPath $path) {
            $t = $line.Trim()
            if ([string]::IsNullOrWhiteSpace($t) -or $t.StartsWith('#')) { continue }
            $eq = $t.IndexOf('=')
            if ($eq -lt 1) { continue }
            $k = $t.Substring(0, $eq).Trim()
            $v = $t.Substring($eq + 1).Trim().Trim('"').Trim("'")
            $hash = $v.IndexOf('#')
            if ($hash -ge 0) { $v = $v.Substring(0, $hash).Trim().Trim('"').Trim("'") }
            if ([string]::IsNullOrWhiteSpace($v)) { continue }
            switch ($k) {
                'account_id' { $script:accountId = $v }
                'license_key' { $script:licenseKey = $v }
                'edition' { $script:edition = $v }
                'download_url' { $script:downloadUrl = $v }
            }
        }
    }
    Read-MaxMindToml $ConstantsFile
    # Overlay gitignored local file (license key lives here; not in tracked TOML).
    $localOverlay = Join-Path (Split-Path -Parent $ConstantsFile) 'maxmind-constants.local.toml'
    Read-MaxMindToml $localOverlay
    if ([string]::IsNullOrWhiteSpace($accountId) -or [string]::IsNullOrWhiteSpace($licenseKey)) {
        Write-Error 'Update-MaxMindGeoLite.ps1: account_id and license_key required (set license_key in maxmind-constants.local.toml)'
        exit 3
    }
    if (-not $downloadUrl) {
        $downloadUrl = "https://download.maxmind.com/geoip/databases/$edition/download?suffix=tar.gz"
    }

    $destFile = Join-Path $DestinationDir 'GeoLite2-Country.mmdb'
    $tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("aic-geolite-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tmpRoot -Force | Out-Null
    try {
        $tarGz = Join-Path $tmpRoot 'geolite.tar.gz'
        Write-Host "Downloading $edition (license key not printed) ..."
        $pair = "${accountId}:${licenseKey}"
        $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
        $headers = @{ Authorization = "Basic $b64" }
        Invoke-WebRequest -Uri $downloadUrl -Headers $headers -OutFile $tarGz -UseBasicParsing -TimeoutSec 180
        tar -xzf $tarGz -C $tmpRoot
        $found = Get-ChildItem -Path $tmpRoot -Recurse -Filter 'GeoLite2-Country.mmdb' | Select-Object -First 1
        if (-not $found) {
            Write-Error 'Update-MaxMindGeoLite.ps1: archive did not contain GeoLite2-Country.mmdb'
            exit 4
        }
        Copy-Item -LiteralPath $found.FullName -Destination $destFile -Force
        $hash = (Get-FileHash -LiteralPath $destFile -Algorithm SHA256).Hash.ToLowerInvariant()
        Set-Content -LiteralPath ($destFile + '.sha256') -Value "$hash  GeoLite2-Country.mmdb`n" -Encoding ascii
        Write-Host "Wrote $destFile (sha256=$hash)"
        Write-Host 'Remember: do not commit the .mmdb to public git (MaxMind license). Run sync-to-projects.ps1 to copy into consumers.'
        exit 0
    } finally {
        Remove-Item -LiteralPath $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
} catch {
    $script = Split-Path -Leaf $PSCommandPath
    Write-Error "${script}: MaxMind GeoLite2 update failed: $_"
    exit 2
}
