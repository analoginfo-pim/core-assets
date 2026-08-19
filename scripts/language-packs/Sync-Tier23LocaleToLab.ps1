param([Parameter(Mandatory)][string]$Tag)
$src = "c:\analog-pim\core-assets\content\locales-ui\$Tag"
$dst = "C:\Program Files\AIC\PimServer\locales\ui\$Tag"
$pd = "C:\ProgramData\AIC\OfflinePimServer\locales\ui\$Tag"
New-Item -ItemType Directory -Force -Path $dst,$pd | Out-Null
Get-ChildItem $src -Filter *.json | Where-Object { $_.Name -notlike '_*' } | ForEach-Object {
  Copy-Item $_.FullName (Join-Path $dst $_.Name) -Force
  Copy-Item $_.FullName (Join-Path $pd $_.Name) -Force
}
Write-Host "synced $Tag ($((Get-ChildItem $dst -Filter *.json).Count) files)"
