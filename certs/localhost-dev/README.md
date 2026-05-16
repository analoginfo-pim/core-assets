# Localhost-Dev Certificate Bundle

This directory is the **single source of truth** for the localhost /
lab development certificates shipped with every AIC Offline PIM build.
Every consumer (Cargo dev runs, MSI installers, CI smoke tests) pulls
these exact bytes through
[`pim-installers/scripts/Sync-DevCerts.ps1`](../../../pim-installers/scripts/Sync-DevCerts.ps1).

> [!CAUTION]
> **These keys are public.** They are checked into git on purpose, in
> the same spirit as `dotnet dev-certs https` or `mkcert -install`, so
> a fresh `cargo run` or `msiexec /i pim-offline-server.msi` works on
> day one. **Never** present them to non-localhost clients, never let
> the `dev-ca.key` leave a developer / CI machine, and **never** ship a
> production deployment without replacing them — anyone holding the CA
> key can forge certs the shipped agents will trust.

## Contents

| File | Role | Algorithm | Validity |
| ---- | ---- | --------- | -------- |
| `dev-ca.crt` / `dev-ca.key` | Self-signed root CA | RSA-4096 / SHA-256 | ~10 years |
| `server.crt` / `server.key` | Server leaf signed by dev-ca | RSA-2048 / SHA-256 | ~10 years |
| `client.crt` / `client.key` | Client leaf signed by dev-ca (CN=`dev-client`) | RSA-2048 / SHA-256 | ~10 years |
| `manifest.json` | SHA-256 fingerprints + validity windows + SAN list | — | regenerated with the bundle |

Server SANs (default): `DNS:localhost`, `DNS:host.docker.internal`,
`IP:127.0.0.1`, `IP:::1`. Use `-ServerSans` when regenerating to add a
lab IPv4 or FQDN if you need the cert to chain for a non-localhost
client on the same subnet.

## How downstream consumers use it

1. **Cargo dev runs** — `pim-offline-server`'s build / dev scripts call
   `Sync-DevCerts.ps1` to mirror the bundle into
   `pim-offline-server/certs/` so the service finds `certs/server.crt`
   / `certs/server.key` on startup without any manual step.
2. **MSI installers** — `Build-PimOfflineServerMsi.ps1` and
   `Build-PimOfflineAgentMsi.ps1` call `Sync-DevCerts.ps1` to stage the
   profile-relevant subset (server: dev-ca + server.{crt,key}; agent:
   dev-ca + client.{crt,key}) into the WiX payload.
3. **WiX install behaviour** — every active cert file (`<INSTALL>\certs\*`)
   is declared with `NeverOverwriteFile="yes"`. Translation:
   - First install -> certs are dropped in from the MSI.
   - Re-install / upgrade with the same shipped defaults still in
     place -> `NeverOverwrite` leaves them, so a stale-default
     replacement happens *only* when an operator explicitly clears
     `<INSTALL>\certs\` first.
   - Re-install / upgrade with an operator-supplied CA-signed cert
     (any contents) -> `NeverOverwrite` preserves the operator's
     files.

   A reference copy is also written to `<INSTALL>\certs\defaults\` on
   every install (refreshed each time), so an operator can `copy
   defaults\*.* ..\` to roll back to the shipped bundle without
   reinstalling.

## Overriding the shipped bundle

The build scripts accept a `-CertOverrideRoot <path>` parameter that
points at a directory laid out exactly like this one (six PEM files +
`manifest.json`). When supplied, `Sync-DevCerts.ps1` validates and
ships those bytes instead of `core-assets/certs/localhost-dev/`.

This is the intended hand-off point for:
- A lab box where the SANs need to bake in a real subnet IPv4.
- A QA build using a longer-lived or HSM-backed CA.
- An air-gapped build where the operator pre-staged the bundle.

## Regenerating the bundle

```powershell
pwsh ./Regenerate-DevCerts.ps1
# or, to bake an additional lab IPv4 / FQDN into server.crt:
pwsh ./Regenerate-DevCerts.ps1 -ServerSans 'IP:192.168.55.197','DNS:lab-pim-01.lab.example'
```

The script:
- Requires OpenSSL 3.x on `PATH` (`winget install ShiningLight.OpenSSL`
  or the OpenSSL bundled with Git for Windows).
- Wipes and rewrites every `*.crt`, `*.key`, `*.srl`, and `manifest.json`
  in place.
- Tolerates an inherited `OPENSSL_CONF` env var that points at a stale
  config (common on Windows boxes with PostgreSQL / Git installs) by
  unsetting it for the duration of the run.
- Emits a manifest.json that the build-time `Sync-DevCerts.ps1` then
  validates with SHA-256, so a corruption-during-copy fails the build
  loudly rather than silently shipping mismatched bytes.

After regenerating, commit the *entire* directory (certs, keys, and
manifest) — downstream builds will pick the new fingerprints up on the
next build without any other changes.

## What's deliberately **not** here

- **Production certs / customer CAs.** Those live in the operator's
  secret store and are loaded at runtime via
  `pim-app-config`'s `TLS_CERT_PATH` / `TLS_KEY_PATH` keys; they never
  appear in this directory or in the MSI payload.
- **Per-customer leaves.** If a customer wants leaf certs signed by
  their own CA, they replace `<INSTALL>\certs\server.{crt,key}` after
  install (`NeverOverwriteFile="yes"` means the operator's file
  survives every subsequent upgrade).
