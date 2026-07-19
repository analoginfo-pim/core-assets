# Threat intelligence blocklists (shared)

Offline IP blocklists for AIC products: offline-server Access Control → Threat
intel, and later Mix / firewall / IDS consumers.

## Feeds

| Directory | Feed | Format |
| --- | --- | --- |
| `firehol/` | FireHOL level1 (blocklist-ipsets) | `firehol.list` — one IP/CIDR per line |
| `et-open/` | Emerging Threats Open block IPs | `et-open.list` |
| `abuseipdb/` | AbuseIPDB export / API blacklist | `abuseipdb.list` |

## Licensing

- **FireHOL** aggregates third-party lists — respect each upstream license.
- **ET Open** — Proofpoint Emerging Threats redistribution terms.
- **AbuseIPDB** — account + Terms of Service; API updates need an operator key
  (never commit AbuseIPDB API keys here). Without a key, `abuseipdb.list` stays
  a small RFC 5737 fixture; with `-DownloadAbuseIpdb` the blacklist snapshot
  (up to the API limit) is the distribution seed.

**FireHOL level1** and **ET Open** full public lists are the default seed for
every AIC Offline Server install (via MSI / Program Files → ProgramData).
Tiny fixtures under product `tools/threat-intel-fixtures/` are for unit tests
only — never for ProgramData.

These lists are intended for **firewall / IDS / access-control** use across
AIC products, not for redistribution outside AIC deployments.

## Refresh

```powershell
cd c:\analog-pim\core-assets
pwsh .\scripts\Update-ThreatIntelLists.ps1 -ConfirmDownload -DownloadFirehol -DownloadEtOpen
# AbuseIPDB (optional, needs API key parameter — never env):
# pwsh .\scripts\Update-ThreatIntelLists.ps1 -ConfirmDownload -DownloadAbuseIpdb -AbuseIpdbApiKey '<key>'
pwsh .\scripts\sync-to-projects.ps1
```

Offline server ProgramData seed:

```powershell
pwsh ..\pim-offline-server\scripts\Update-ThreatIntelLists.ps1 `
  -SourceDir ..\pim-offline-server\assets\threat-intel
# or after sync:
pwsh ..\pim-offline-server\scripts\Seed-GeoIpAndThreatIntelFromAssets.ps1
```
