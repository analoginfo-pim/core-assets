# GeoIP (MaxMind GeoLite2)

Shared MaxMind GeoLite2 assets for AIC products (offline server Access Map,
future Mix / firewall / IDS country lookups).

## Layout

| Path | Purpose |
| --- | --- |
| `maxmind-constants.toml` | Account ID + edition URL (**no license key** — git-safe) |
| `maxmind-constants.local.toml` | Gitignored license key overlay (lab/build only) |
| `maxmind-constants.local.toml.example` | Template for the local overlay |
| `GeoLite2-Country.mmdb` | Country MMDB binary (**not committed** — MaxMind license) |
| `GeoLite2-Country.mmdb.sha256` | Optional checksum written by the update script |

## Approach: ship the real MMDB (not an extracted table)

AIC packages the **full GeoLite2-Country.mmdb** (~9 MB) in the offline-server
MSI under `ProgramFiles\...\geoip\`. First boot / db-init / lab restore copy it
into `%ProgramData%\AIC\OfflinePimServer\geoip\` when missing. On-demand
Download/Import refresh replaces the ProgramData MMDB. No CSV/SQLite extract.

## MaxMind license obligations

- GeoLite2 requires a free MaxMind account and license key.
- Put the license key only in `maxmind-constants.local.toml` (gitignored) or
  stage via `Stage-MaxMindGeoLiteDefaults.ps1` / `maxmind-defaults.local.toml`
  in pim-offline-server. GitHub push protection rejects committed keys.
- Do **not** redistribute the `.mmdb` outside AIC product channels without a
  MaxMind redistribution license. Attribute MaxMind / GeoLite2 where required.
- Do not log or display the license key in UIs.
- Credentials are for **on-demand Download/Update only**; first start uses the
  shipped MMDB bytes (no network).

## Refresh procedure

```powershell
cd c:\analog-pim\core-assets
# Once: copy maxmind-constants.local.toml.example → .local.toml and set license_key
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Update-MaxMindGeoLite.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Update-ThreatIntelLists.ps1 -ConfirmDownload -DownloadFirehol -DownloadEtOpen
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\sync-to-projects.ps1
```

## MSI / first-boot

| Install path | ProgramData (runtime) |
| --- | --- |
| `%ProgramFiles%\AIC\OfflinePimServer\geoip\GeoLite2-Country.mmdb` | `%ProgramData%\AIC\OfflinePimServer\geoip\GeoLite2-Country.mmdb` |
| `...\threat-intel\*.list` | `...\threat-intel\*.list` |

On first service boot, `db-init`, and lab restore, missing ProgramData files are
copied from the install-tree seed (never overwriting operator updates).
On-demand refresh: Access Control UI Download/Import + scripts.

## Sync destinations

`scripts/sync-to-projects.ps1` copies constants, MMDB (when present), and
flattened TI lists into `pim-offline-server/assets/` and `pim-installers/assets/`.
