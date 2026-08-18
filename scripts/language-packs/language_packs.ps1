# Thin wrapper — all logic is in language_packs.py (Python 3 stdlib).
# Usage: .\language_packs.ps1 hash
#        .\language_packs.ps1 audit --product aic-server
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ArgsRest
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Py = Join-Path $Root 'scripts\language-packs\language_packs.py'
$python = $null
foreach ($c in @('py', 'python3', 'python')) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source; break }
}
if (-not $python) {
    Write-Error 'Python 3 is required. Install CPython 3 and re-run.'
}
if ($python -like '*\py.exe' -or $python -eq 'py') {
    & py -3 $Py --root $Root @ArgsRest
} else {
    & $python $Py --root $Root @ArgsRest
}
exit $LASTEXITCODE
