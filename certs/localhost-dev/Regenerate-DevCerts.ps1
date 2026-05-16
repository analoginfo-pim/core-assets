<#
.SYNOPSIS
    Regenerate the canonical localhost-dev certificate bundle (root CA +
    server leaf + client leaf) shipped with `core-assets`.

.DESCRIPTION
    Produces six PEM files plus a manifest.json in $OutputDir (default:
    the script's own directory). The bundle is intended for **localhost
    development and CI smoke tests only** — every consumer that picks it
    up does so via `pim-installers/scripts/Sync-DevCerts.ps1`, and every
    end-user installer (MSI) ships the same bytes so a fresh `cargo run`
    or `msiexec /i pim-offline-server.msi` works out of the box without
    any pre-step.

    Cert layout:
      - dev-ca.{crt,key} : self-signed root CA, RSA-4096, SHA-256, ~10y
        validity. Carries cRLSign + keyCertSign and BasicConstraints
        CA:TRUE,pathlen:1 so it can issue intermediates if we ever need
        them.
      - server.{crt,key} : RSA-2048 leaf signed by dev-ca, ServerAuth +
        ClientAuth EKU, multi-SAN (localhost, host.docker.internal,
        127.0.0.1, ::1).
      - client.{crt,key} : RSA-2048 leaf signed by dev-ca, ClientAuth
        EKU, CN=dev-client (used by the future mTLS path on agents).

    Then computes SHA-256 of each file and emits manifest.json with the
    fingerprints, validity windows, SAN list, and the script version.

    !! These keys are CHECKED IN ON PURPOSE and are PUBLIC. Treat them
    like the `dotnet dev-certs https` / `mkcert -install` bundles — they
    exist so localhost works on day one. NEVER use them in production or
    over the public internet; the dev-ca.key in particular would let any
    holder forge certs that the shipped agents trust.

.PARAMETER OutputDir
    Directory to write the cert bundle into. Defaults to the script's
    own directory (`core-assets/certs/localhost-dev/`).

.PARAMETER ServerSans
    Extra Subject Alternative Names to add to server.crt on top of the
    built-in set (localhost, host.docker.internal, 127.0.0.1, ::1).
    Use `dns:foo.example` or `ip:1.2.3.4` syntax (case-insensitive).
    Useful when a lab box needs its real IPv4 baked into the leaf
    without rewriting the script.

.PARAMETER ValidityYears
    Validity period for all three certs, in years. Defaults to 10.

.PARAMETER OpenSslExe
    Path to `openssl.exe`. Defaults to whatever is on `PATH` (the
    OpenSSL 3.x install that ships with Git for Windows or the
    OpenSSL-Win64 MSI both work).

.EXAMPLE
    pwsh ./Regenerate-DevCerts.ps1
    # Refresh the bundle in place.

.EXAMPLE
    pwsh ./Regenerate-DevCerts.ps1 -ServerSans 'IP:192.168.55.197','DNS:lab-pim-01.lab.example'
    # Add a lab IPv4 + FQDN so the cert chains for a non-localhost
    # client on the same subnet.
#>
[CmdletBinding()]
param(
    [string]$OutputDir = '',
    [string[]]$ServerSans = @(),
    [int]$ValidityYears = 10,
    [string]$OpenSslExe = 'openssl'
)

$ErrorActionPreference = 'Stop'

# `$PSScriptRoot` is only reliably populated inside the script body,
# not at parameter-binding time (it can be empty when the script is
# invoked from a different runspace). Resolve the default here.
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    if ($PSScriptRoot) {
        $OutputDir = $PSScriptRoot
    } else {
        $OutputDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -Path $OutputDir -ItemType Directory -Force | Out-Null
}

# Sanity-check openssl is present and is the 3.x series (older 1.1
# release lines don't support `x509 -copy_extensions` cleanly).
$opensslVersion = & $OpenSslExe version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "openssl not found at '$OpenSslExe'. Install OpenSSL 3.x (winget install ShiningLight.OpenSSL) and retry."
}
if ($opensslVersion -notmatch 'OpenSSL\s+3\.') {
    Write-Warning "Detected '$opensslVersion'. Script is tested with OpenSSL 3.x; older releases may produce slightly different output but should still work."
}

# On Windows we frequently inherit an `OPENSSL_CONF` env var pointing
# at the Postgres-ODBC or git-for-windows config files (which may not
# even exist on disk on a given dev box). The CertificateRequest path
# we use here doesn't need any of those tunables, so wipe the env var
# for the duration of this script — the openssl built-in defaults
# work fine.
$savedOpensslConf = $env:OPENSSL_CONF
$env:OPENSSL_CONF = $null
try {

$nowUtc = [DateTime]::UtcNow

# ---------------------------------------------------------------
# 1) Root CA
# ---------------------------------------------------------------
$caKey = Join-Path $OutputDir 'dev-ca.key'
$caCrt = Join-Path $OutputDir 'dev-ca.crt'
$caSrl = Join-Path $OutputDir 'dev-ca.srl'

Write-Host "[1/3] Generating root CA -> $caCrt"

$caSubject = '/C=US/ST=California/O=Analog Informatics Corporation/OU=AIC Offline PIM (dev)/CN=AIC Offline PIM Localhost Dev Root CA'

& $OpenSslExe req -x509 `
    -nodes `
    -newkey rsa:4096 `
    -sha256 `
    -days ($ValidityYears * 365) `
    -subj $caSubject `
    -addext 'basicConstraints=critical,CA:TRUE,pathlen:1' `
    -addext 'keyUsage=critical,cRLSign,keyCertSign' `
    -addext 'subjectKeyIdentifier=hash' `
    -keyout $caKey `
    -out $caCrt
if ($LASTEXITCODE -ne 0) { throw "openssl req (CA) failed with exit code $LASTEXITCODE" }

# ---------------------------------------------------------------
# 2) Server leaf (SAN: localhost, 127.0.0.1, ::1, + caller extras)
# ---------------------------------------------------------------
$serverKey = Join-Path $OutputDir 'server.key'
$serverCsr = Join-Path $OutputDir 'server.csr'
$serverCrt = Join-Path $OutputDir 'server.crt'
$serverExt = Join-Path $OutputDir 'server.ext'

Write-Host "[2/3] Generating server leaf -> $serverCrt"

$baseServerSans = @(
    'DNS:localhost',
    'DNS:host.docker.internal',
    'IP:127.0.0.1',
    'IP:::1'
)
$allServerSans = @($baseServerSans) + @($ServerSans | Where-Object { $_ -and $_.Trim().Length -gt 0 })
$serverSanLine = ($allServerSans -join ',')

$serverExtContents = @"
subjectAltName=$serverSanLine
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth,clientAuth
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
"@
Set-Content -LiteralPath $serverExt -Value $serverExtContents -Encoding ASCII

& $OpenSslExe req -new `
    -nodes `
    -newkey rsa:2048 `
    -sha256 `
    -subj '/C=US/ST=California/O=Analog Informatics Corporation/OU=AIC Offline PIM (dev)/CN=localhost' `
    -keyout $serverKey `
    -out $serverCsr
if ($LASTEXITCODE -ne 0) { throw "openssl req (server csr) failed with exit code $LASTEXITCODE" }

# Note: we deliberately let -CAcreateserial pick the serial. Combining
# `-set_serial` with `-CAcreateserial` causes openssl 3 to reject the
# explicit value ("bn dec2bn error") because the random-vs-explicit
# code paths fight over the .srl ledger. The ledger-managed serial is
# unique-per-issue anyway.
& $OpenSslExe x509 -req `
    -in $serverCsr `
    -CA $caCrt `
    -CAkey $caKey `
    -CAcreateserial `
    -CAserial $caSrl `
    -days ($ValidityYears * 365) `
    -sha256 `
    -extfile $serverExt `
    -out $serverCrt
if ($LASTEXITCODE -ne 0) { throw "openssl x509 (server) failed with exit code $LASTEXITCODE" }

Remove-Item -LiteralPath $serverCsr, $serverExt -ErrorAction SilentlyContinue

# ---------------------------------------------------------------
# 3) Client leaf (CN=dev-client, ClientAuth EKU, no SAN)
# ---------------------------------------------------------------
$clientKey = Join-Path $OutputDir 'client.key'
$clientCsr = Join-Path $OutputDir 'client.csr'
$clientCrt = Join-Path $OutputDir 'client.crt'
$clientExt = Join-Path $OutputDir 'client.ext'

Write-Host "[3/3] Generating client leaf -> $clientCrt"

$clientExtContents = @"
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature
extendedKeyUsage=clientAuth
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
"@
Set-Content -LiteralPath $clientExt -Value $clientExtContents -Encoding ASCII

& $OpenSslExe req -new `
    -nodes `
    -newkey rsa:2048 `
    -sha256 `
    -subj '/C=US/ST=California/O=Analog Informatics Corporation/OU=AIC Offline PIM (dev)/CN=dev-client' `
    -keyout $clientKey `
    -out $clientCsr
if ($LASTEXITCODE -ne 0) { throw "openssl req (client csr) failed with exit code $LASTEXITCODE" }

& $OpenSslExe x509 -req `
    -in $clientCsr `
    -CA $caCrt `
    -CAkey $caKey `
    -CAserial $caSrl `
    -days ($ValidityYears * 365) `
    -sha256 `
    -extfile $clientExt `
    -out $clientCrt
if ($LASTEXITCODE -ne 0) { throw "openssl x509 (client) failed with exit code $LASTEXITCODE" }

Remove-Item -LiteralPath $clientCsr, $clientExt -ErrorAction SilentlyContinue

# ---------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------
function Get-FileSha256 {
    param([string]$Path)
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-CertValidity {
    param([string]$CertPath)
    # `openssl x509 -enddate` formats like "notAfter=May 16 09:43:18 2026 GMT".
    # Ask openssl for an ISO 8601 / UTC form instead so we don't fight
    # `[DateTime]::Parse` with a non-canonical month abbreviation +
    # explicit "GMT" suffix.
    $startUtc = & $OpenSslExe x509 -in $CertPath -noout -startdate -dateopt iso_8601 2>$null
    $endUtc   = & $OpenSslExe x509 -in $CertPath -noout -enddate   -dateopt iso_8601 2>$null
    $parse = {
        param($line, $prefix)
        if ($line -and $line.StartsWith($prefix)) {
            $s = $line.Substring($prefix.Length).Trim()
            # iso_8601 emits e.g. "2026-05-16 09:43:18Z"; treat as UTC.
            try { return ([DateTime]::Parse($s, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal)).ToString('o') }
            catch { return $null }
        }
        $null
    }
    [ordered]@{
        not_before = & $parse $startUtc 'notBefore='
        not_after  = & $parse $endUtc   'notAfter='
    }
}

$files = @(
    [ordered]@{ name = 'dev-ca.crt'; role = 'root-ca-cert' },
    [ordered]@{ name = 'dev-ca.key'; role = 'root-ca-key' },
    [ordered]@{ name = 'server.crt'; role = 'server-leaf-cert' },
    [ordered]@{ name = 'server.key'; role = 'server-leaf-key' },
    [ordered]@{ name = 'client.crt'; role = 'client-leaf-cert' },
    [ordered]@{ name = 'client.key'; role = 'client-leaf-key' }
)

$fileEntries = foreach ($f in $files) {
    $p = Join-Path $OutputDir $f.name
    $entry = [ordered]@{
        name   = $f.name
        role   = $f.role
        sha256 = Get-FileSha256 -Path $p
        size   = (Get-Item -LiteralPath $p).Length
    }
    if ($f.name -match '\.crt$') {
        $validity = Get-CertValidity -CertPath $p
        $entry['not_before'] = $validity.not_before
        $entry['not_after']  = $validity.not_after
    }
    $entry
}

$manifest = [ordered]@{
    schema           = 'analoginfo.localhost-dev-certs.v1'
    generator        = 'core-assets/certs/localhost-dev/Regenerate-DevCerts.ps1'
    generator_version = '1.0.0'
    generated_at_utc = $nowUtc.ToString('o')
    validity_years   = $ValidityYears
    server_sans      = $allServerSans
    purpose          = 'Localhost / lab development & CI smoke tests. Not for production.'
    files            = $fileEntries
}

$manifestPath = Join-Path $OutputDir 'manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

    Write-Host ""
    Write-Host "Done. Bundle in: $OutputDir"
    Write-Host "Server SANs:    $serverSanLine"
    Write-Host "Manifest:       $manifestPath"
    Write-Host ""
    Write-Host "Next:"
    Write-Host "  1. git add core-assets/certs/localhost-dev"
    Write-Host "  2. git commit -m 'core-assets: refresh localhost-dev certs'"
    Write-Host "  3. Downstream consumers automatically pick up the new bundle"
    Write-Host "     on the next build (pim-installers/scripts/Sync-DevCerts.ps1)."
}
finally {
    $env:OPENSSL_CONF = $savedOpensslConf
}
