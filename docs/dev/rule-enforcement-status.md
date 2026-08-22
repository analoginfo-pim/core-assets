# Workspace rule enforcement status (point-in-time)

This document holds the **point-in-time adoption status** that used to
live inside `.cursor/rules/*.mdc` files as "Where this is currently
enforced" matrices.

Those matrices were injected into every agent conversation on every turn
and cost real context budget while rarely changing agent behavior. The
**contract** — the rule statement, forbidden constructs, required
patterns, and required agent behavior — stays in the rule file, which is
what an agent needs in order to write correct code. The **status** lives
here, which is what a human needs in order to plan work.

Nothing in this document relaxes, narrows, or adds an exception to any
rule. A row marked "audit ongoing" or "partial" means *unverified*, and
for certification purposes unverified is equivalent to defective until a
verification is recorded.

Last consolidated: 2026-08-15.

---

## Shutdown compliance

Rule: [`shutdown-compliance.mdc`](../../.cursor/rules/shutdown-compliance.mdc)

| Repo | Class | Compliant today? |
| --- | --- | --- |
| `pim-offline-server` (Windows SCM) | service | partial; SCM state-machine fix in flight |
| `pim-offline-server` (Linux/macOS daemon) | service | audit ongoing |
| `pim-offline-client` (Windows SCM) | service | partial; same fix |
| `pim-offline-client` (Linux/macOS daemon) | service | audit ongoing |
| `pim-offline-server-configurator-tauri` | GUI | audit ongoing |
| `pim-offline-client-configurator-tauri` | GUI | audit ongoing |
| `pim-offline-client-elevate-tauri` | GUI (modal) | audit ongoing |
| `pim-offline-server-configurator-win32` | GUI | audit ongoing |
| `pim-offline-client-configurator-win32` | GUI | audit ongoing |
| `pim-offline-client-elevate-win32` | GUI (modal) | audit ongoing |
| `pim-product-launcher-slint` | GUI | audit ongoing |
| `pim-product-launcher-win32` | GUI | audit ongoing |
| `pim-app-config-cli` | CLI | audit ongoing |
| `pim-offline-agent-configurator-cli` | CLI | audit ongoing |
| `pim-offline-server-configurator` (CLI) | CLI | audit ongoing |
| `db-init` (in `pim-offline-server`) | CLI (destructive) | audit ongoing — highest priority for Ctrl+C handling |

Every binary touched must gain a row in `docs/ops/shutdown-compliance.md`
(workspace root) recording application class, handler file:line,
per-component budgets, and manual verification steps.

---

## Service lifecycle logs (41010 / 41011 / 41012)

Rule: [`service-lifecycle-logs.mdc`](../../.cursor/rules/service-lifecycle-logs.mdc)

| Binary | Status |
| --- | --- |
| `pim-offline-server` (Windows SCM + systemd) | partial — emits PROCESS_STARTED / PROCESS_STOPPED; service-lifecycle triplet pending |
| `pim-offline-agent` (Windows SCM + systemd + launchd) | partial — same |
| `pim-offline-{client,server}-configurator-{win32,tauri}` | n/a — not services; they emit per-action audit events |
| `pim-offline-client-elevate-{win32,tauri}` | n/a — modal helpers |
| `pim-product-launcher-{slint,win32}` | n/a — not services |
| `pim-windows-oplog::ids::SERVICE_{STARTED,STOPPING,STOPPED}` | new — Wave 1 ID allocation; message catalog entry pending |

---

## runtime-status.json

Rule: [`runtime-status.mdc`](../../.cursor/rules/runtime-status.mdc)

| Surface | Status |
| --- | --- |
| `pim-offline-client/src/runtime_status.rs` (writer) | enacted; schema 2; tests at three layers |
| `pim-offline-server/src/runtime_status.rs` (writer) | enacted in Wave 4 Track I; schema 2; tests at three layers; R7 violation closed |
| `pim-offline-client/tests/runtime_status.rs` | 9/9 passing |
| `pim-offline-server/tests/runtime_status.rs` | 12/12 passing |
| `pim-installers/test/soak.Tests.ps1` | 7/7 SelfCheck passing; live-soak asserts schema-2 fields |
| `pim-offline-client/src/win_scm_dispatch.rs` | publishes `record_signal_received` / `record_drain_outcome` |
| `pim-offline-server/src/bin/server/win_scm_dispatch.rs` | same, via process-singleton |
| Per-product docs | `pim-offline-{client,server}/docs/dev/runtime-status.md` — schema 2 field reference |

---

## Runtime status placeholder fingerprints (R7)

Rule: [`runtime-status-flags-test-fixtures.mdc`](../../.cursor/rules/runtime-status-flags-test-fixtures.mdc)

| Surface | Status |
| --- | --- |
| `pim-offline-client/src/runtime_status.rs` (`RuntimeStatusSnapshot`, writer) | exists — Wave 1 Track C adds `fingerprint_warnings` |
| `pim-offline-server` analogue | audit ongoing — Wave 1 Track C |
| `pim-offline-client-configurator-{win32,tauri}` warnings badge | audit ongoing — Wave 2 Track E |
| `pim-offline-server-configurator-{win32,tauri}` warnings badge | audit ongoing — Wave 2 Track E |

---

## Bounded network I/O in drains (R4)

Rule: [`bounded-network-io-in-drains.mdc`](../../.cursor/rules/bounded-network-io-in-drains.mdc)

| Binary | Has bounded helper? | All call sites use it? |
| --- | --- | --- |
| `pim-offline-client` (`HttpClient::execute_with_budget`) | yes (Wave 1 Track D in flight) | partial |
| `pim-offline-server` (update checks, OTLP) | partial — OTLP exporter wraps in its own timeout; update-feed client audit ongoing | partial |
| `pim-offline-client-configurator-{win32,tauri}` connectivity test | yes, via `run_offline_server_probe` | yes |
| `pim-offline-server-configurator-{win32,tauri}` connectivity test | yes, via `run_postgres_probe` | yes |
| `pim-offline-client-elevate-{win32,tauri}` | n/a — IPC only, no HTTP |

---

## Manifest gates every storage write (R2)

Rule: [`manifest-gates-storage-writes.mdc`](../../.cursor/rules/manifest-gates-storage-writes.mdc)

| Surface | Status |
| --- | --- |
| `AppConfigError::UnknownKey` variant | enacted, `crates/pim-app-config/src/error.rs` |
| `AppConfig::set_value` refuses unknown keys | enacted, `crates/pim-app-config/src/app_config.rs:192` |
| `AppConfig::unset_value` refuses unknown keys | audit ongoing — Wave 1 Track F |
| `pim-app-config-cli` `set` / `unset` exit codes | audit ongoing — Wave 1 Track F |
| `pim-offline-agent-configurator-cli`, `pim-offline-server-configurator` | inherit Track F |
| All four configurator GUI Save flows | audit ongoing |
| `orphans` subcommand | not yet implemented — required before the next MSI version bump |

---

## Single source of truth for settings (R3)

Rule: [`single-source-of-truth-for-settings.mdc`](../../.cursor/rules/single-source-of-truth-for-settings.mdc)

| Binary | Status |
| --- | --- |
| `pim-offline-server` | compliant — greenfield, single store |
| `pim-offline-agent` | partial — runtime resolver still consults `settings.json` on some paths; Wave 1 Track C owns the fix |
| `pim-offline-client-configurator-{win32,tauri}` | inherits the agent's compliance |
| `pim-offline-server-configurator-{win32,tauri}` | compliant — writes only via `AppConfig::set_value` |
| `pim-offline-client-elevate-{win32,tauri}` | n/a — no settings store |

---

## Manifest defaults must be realistic (R5)

Rule: [`manifest-defaults-must-be-realistic.mdc`](../../.cursor/rules/manifest-defaults-must-be-realistic.mdc)

| Manifest | Status |
| --- | --- |
| `pim-offline-client/app-config.toml` | partial — Wave 1 Track C audits each `default_dev` against the smoke loop |
| `pim-offline-server/app-config.toml` | partial — same review pass |
| `pim-app-config` sample manifest | exempt (sample, not a shipping product) |

---

## Placeholder GUIDs are empty (R6)

Rule: [`placeholder-guids-are-empty.mdc`](../../.cursor/rules/placeholder-guids-are-empty.mdc)

| Surface | Status |
| --- | --- |
| `pim_app_config::normalize_legacy_guid_sentinel` | not yet implemented — Wave 1 Track F |
| `pim-offline-agent` `AGENT_UUID` validator | partial — Wave 1 Track C audit pending |
| `pim-offline-server` `DEFAULT_TENANT_GUID` validator | partial — Wave 1 Track C audit pending |
| All four configurator GUI Save flows | inherits the R2 manifest validator |
| SQL upserts in `pim-offline-server/src/db/` | audit ongoing — no `"0"` fallbacks in current code |
| Legacy `settings.json` migration path | runs the normalizer per key before `set_value` |

---

## No JSON documents in platform storage

Rule: [`no-json-in-platform-storage.mdc`](../../.cursor/rules/no-json-in-platform-storage.mdc)

| Surface | Status |
| --- | --- |
| `pim-app-config` (`scalar_value.rs`, `AppConfig::set`, `set_secret_extra`) | enacted |
| `pim-app-config` (`settings_import::import_settings_file`) | enacted — scalar keys via `json_value_to_scalar_string` |
| `pim-app-config-cli` `set` / embedded configurators | enacted — inherits the `AppConfig::set` gate |
| `pim-offline-client` `app_config_bridge::persist_from_settings` | enacted |
| `pim-offline-client` enrollment token import (scalar id/shape extras) | enacted — legacy JSON meta migration |
| `pim-config-storage` backends | compliant by API shape (`put` takes scalar strings) |
| `pim-offline-server` app-config bridge / import | audit ongoing — must mirror the agent pattern |
| `pim-offline-*-configurator-{win32,tauri}` Save flows | enacted via in-process `AppConfig::set` |

---

## FIPS DLL staging

Rule: [`fips-dll-staging.mdc`](../../.cursor/rules/fips-dll-staging.mdc)

Binary crates that link `aws-lc-rs/fips` and therefore need the
`stage_aws_lc_fips_dll` helper in their `build.rs`:

| Repo | Binaries |
| --- | --- |
| `pim-offline-server` | `pim-offline-server.exe`, `pim-offline-server-configurator.exe`, `db-init.exe`, … |
| `pim-offline-client` | `pim-offline-agent.exe`, `pim-offline-agent-configurator-cli.exe` |
| `pim-offline-server-configurator-win32` | `pim-offline-server-configurator-win32.exe` |
| `pim-offline-server-configurator-tauri` | `pim-offline-server-configurator-tauri.exe` |
| `pim-offline-client-configurator-win32` | `pim-offline-client-configurator-win32.exe` |
| `pim-offline-client-configurator-tauri` | `pim-offline-client-configurator-tauri.exe` |
| `pim-offline-client-elevate-win32` | `pim-offline-client-elevate-win32.exe` |
| `pim-offline-client-elevate-tauri` | `pim-offline-client-elevate-tauri.exe` |

---

## No-panic policy: per-repo lint adoption

Rule: [`no-panic.mdc`](../../.cursor/rules/no-panic.mdc)

| Repo | Per-crate clippy lint table present? |
| --- | --- |
| `pim-offline-client` | yes |
| `pim-offline-server` | yes |
| `pim-app-config` | workspace-wide |
| `pim-orm-offline` | partial (per its AGENTS.md no-panic line) |
| `pim-orm` | not yet — add when next touching |
| `pim-ui-kit` (TS) | not yet — add eslint rules when next touching |
| `pim-offline-legacy-client` (Python) | not yet — add ruff rules when next touching |
| All `pim-offline-{client,server}-{configurator,elevate}-{tauri,win32}` | none |
| `pim-product-launcher-{slint,win32}` | none |
| `pim-installers` (PowerShell + WiX) | n/a — PowerShell guidance applies |

When you touch a repo whose Cargo / package config lacks the lint table,
add it as part of that change set.

---

## Silent failure is a bug: per-surface adoption

Rule: [`silent-failure-is-a-bug.mdc`](../../.cursor/rules/silent-failure-is-a-bug.mdc)

| Surface | Status |
| --- | --- |
| `pim-offline-client` service scheduler | Wave 1 Track D adds the structured error-log shape |
| `pim-offline-client` HTTP client error handling | Wave 1 Track D |
| `pim-offline-server` admin API handlers | partial — structured at the route-handler level; inner-helper audit ongoing |
| `pim-offline-server` background jobs (audit log writer, OTLP exporter) | audit ongoing |
| All four configurator GUIs | inherits library logging shape via `pim_app_config_cli::dialog_helpers` |
| `pim-app-config` CLI (`set` / `unset` / `get` / `orphans`) | inherits via R2 exit codes |

---

## Tests must not touch machine state (R1)

Rule: [`tests-must-not-touch-machine-state.mdc`](../../.cursor/rules/tests-must-not-touch-machine-state.mdc)

| Repo | Status |
| --- | --- |
| `pim-offline-client` (`Settings`, `RuntimeStatus`, IPC paths) | partial — fixture APIs in flight under Wave 1 Track C |
| `pim-offline-server` (`AdminAuth`, legacy compat, seed-dev) | partial — `AdminAuth::with_token` exists; `ENABLE_LEGACY_COMPAT` tests still mutate env |
| `pim-app-config` / `pim-app-config-i18n` | audit ongoing — `Locale::override_for_tests` planned |
| `pim-config-storage` | compliant — in-memory backend exists; tests must select it explicitly |
| Sibling configurator / elevation crates | inherit fixture APIs from the libraries above |

### Production env vars still read (fixture-replacement inventory)

Refresh with:
`rg "env::var(_os)?\(\s*\"(OFFLINE_|AIC_|PIM_|LOCAL_UPDATE_|ENABLE_LEGACY_|OFFLINE_DEV_|OFFLINE_ADMIN_)" --type rust`

| Env var | Read by | Fixture replacement |
| --- | --- | --- |
| `OFFLINE_DEBUG_LOG_DIR` | `pim-offline-client/src/config/settings.rs:326` | `Settings::log_dir_for_tests(&Path)` |
| `OFFLINE_DEBUG_CONFIG_DIR` | `pim-offline-client/src/config/settings.rs:401` | `Settings::save_to_file_at(&Path)` / `load_from_dir(&Path)` |
| `OFFLINE_DEBUG_RUNTIME_STATUS_DIR` | `pim-offline-client/src/runtime_status.rs:197` | `RuntimeStatus::write_to_dir(&Path)` |
| `PIM_OFFLINE_IPC_ELEVATION_PATH` | `pim-offline-client/src/ipc/paths.rs:38,45` | `IpcServer::bind_at(&str)` + `IpcClient::connect_at(&str)` |
| `OFFLINE_DEV_FIXTURES` | `pim-offline-server/src/bin/seed_dev/main.rs:106` | seed-dev is a binary; tests must not import it |
| `OFFLINE_ADMIN_TOKEN` | `pim-offline-server/src/auth/admin.rs` | `AdminAuth::with_token(&str)` |
| `ENABLE_LEGACY_COMPAT` | `pim-offline-server/src/api/legacy/…` | `LegacyTranslator::enabled(bool)` |
| `UI_LOCALE` / `resolve_locale` | `pim-app-config/crates/pim-app-config-i18n/src/locale.rs` | Explicit preference arg + OS UI language; no `PIM_LOCALE` env (fixture: `resolve_locale(Some("de"))`) |

Any new env-var read must arrive with its fixture API in the same change
set, and this table must be updated.

---

## FIPS crypto posture: measured dependency state

Rule: [`enterprise-compliance.mdc`](../../.cursor/rules/enterprise-compliance.mdc) §4

Measured 2026-08-05 (G-FIPS-RING tree-clean), `cargo tree -i ring --target all`:

| Binary | TLS provider (track) | aws-lc-rs linked | ring linked |
| --- | --- | --- | --- |
| `pim-offline-server` | rustls + aws-lc-rs (A) | yes | **NO — clean** |
| `pim-offline-client` (agent) | native-tls (B) | no | **NO — clean** |
| `pim-offline-client-configurator-win32` | rustls + aws-lc-rs (A) | yes | **NO — clean** |
| `pim-offline-client-configurator-tauri` | rustls + aws-lc-rs (A) | yes | **NO — clean** |
| `pim-offline-client-elevate-win32` | none (IPC only) | no | **NO — clean** |
| `pim-offline-client-elevate-tauri` | none (IPC only) | no | **NO — clean** |
| `pim-offline-server-configurator-win32` | rustls + aws-lc-rs (A) | yes | **NO — clean** |
| `pim-offline-server-configurator-tauri` | rustls + aws-lc-rs (A) | yes | **NO — clean** |

Server tree-clean path: russh → `aws-lc-rs` (not `ring`);
`pim-events-destinations` / reqwest → `rustls-tls-*-no-provider`;
`pim-app-config` ureq without `tls` (custom PEM via reqwest);
`pim-orm*` / `pim-orm-jobs` path-patched to `tls-rustls-aws-lc-rs`.
Evidence: `pim-offline-server/docs/dev/fips-ring-posture.md`.

Re-run `cargo tree -i ring --target all` after any dependency or feature
change that could reintroduce `ring`.

**Remaining honesty caveats (not `ring`):**

1. Residual non-FIPS `aws-lc-sys` may still compile via upstream feature
   unification. Runtime calls route through the FIPS module
   (aws-lc-rs's internal `cfg_if!` gate), so the CMVP boundary is
   unaffected — but the redundant compilation is real and tracked.
2. `pim-orm-jobs` tag `v0.1.9` still ships `tls-native-tls` until
   Robert retags `fix/sqlx-aws-lc-fips`; Offline carries a path patch
   until then.

### FIPS completion checklist

1. ~~Drive `ring` out of `pim-offline-server`~~ **DONE 2026-08-05.**
   Remaining: Robert's retag of `pim-orm-jobs` so the path patch can drop.
2. ~~Enable the `aws-lc-rs/fips` feature~~ **DONE May 2026, superseded** —
   the feature was removed entirely; FIPS is now wired directly into the
   `rustls` and `aws-lc-rs` dependency declarations across all 10 crates
   with no feature gate. Remaining work: a CI gate rejecting any PR that
   reintroduces a non-FIPS code path.
3. Pin exact module versions (replace "pending" with concrete
   `aws-lc-sys` version, CMVP cert number, and validation date per track).
4. Add a workspace `cargo deny` rule plus a per-binary `forbid_ring`
   integration test.
5. Introduce the application-crypto provider seam (Workstream B) — see
   the rule's §4 for the non-negotiable constraints (every adapter
   carries its own CMVP cert; the provider-routable vs always-local
   operation split; agents stay in-process).
6. Update the rule and this document with the post-completion
   measurement and drop the "pending" qualifiers.

---

## Essential UI actions must be visible: per-page verification

Rule: [`essential-ui-actions-must-be-visible.mdc`](../../.cursor/rules/essential-ui-actions-must-be-visible.mdc)

| Surface | Status |
| --- | --- |
| `ui/src/pages/CurrentStateCompliancePage.tsx` | remediation in flight — clamped cells + pinned actions landed; bounding-box spec pending |
| `ui/e2e/current-state-compliance-embedded-live.spec.ts` | partial — asserts behavior (D1-D9), not geometry |
| `ui/src/components/dataGrid/ReportDataGrid.tsx` | shared wrapper; right place for a future default `getRowHeight` guard |
| Other admin grids (`UserGroupsPage`, `PamEntitlementsPage`, `SessionRecordingsPage`, `RolesCatalogPanel`, …) | already on `autoHeight` + `getRowHeight={() => 'auto'}` — compliant by pattern, unverified by assertion |
| Remaining admin pages | audit ongoing — every page needs one viewport assertion |
| Win32 / Tauri configurator dialogs | inherit the "primary action visible" clause; verified by `scripts/audit-section-508.ps1` plus screenshots |

RCA and phased fix plan:
`pim-offline-server/docs/dev/current-state-compliance-layout-rca.md`.

---

## Workforce identity and assessment readiness: delivery status

Rule: [`workforce-identity-and-assessment-readiness.mdc`](../../.cursor/rules/workforce-identity-and-assessment-readiness.mdc)

Honest status as verified 2026-08-08, so a future agent does not mistake
a table for a feature. Detail:
`pim-offline-server/docs/dev/training-awareness-packs.md`.

| Capability | Status |
| --- | --- |
| Roster of employees and contractors, with vendor organization and archive semantics | **Live** (code) / **Partial** not served — domain + API + UI on `origin/main`; running binary `57715d1fc` predates this |
| Append-only attestation ledger bound to the person record, denormalizing signer identity and document hash at signing | **Live** (code) / **Partial** not served — `operator_recorded` only; no trainee portal |
| Single-use emailed access tokens (trainee needs no console seat) | **Schema only** (`003000048`) |
| Notification ladder (welcome / reminder / due / overdue) with append-only send log | **Live** (code) / **Partial** not served — training sweeper SMTP + log; coverage-intake sweep now SMTP + log (`sent`/`failed`/`suppressed`). Mailpit observation BLOCKED until served |
| Access gate that can block on incomplete training with a recorded override reason | **Schema only** (`003000049`) |
| Document library (plain-language rewrite in progress) | **Live** (authoring layer) |
| Scope determinations — basis, decider, timestamp, review date, rationale, considered exclusions | **Live** (code) / **Partial** not served — `POST` workforce scope routes write `003000050` |
| Identity bindings — plural per person, federated keyed on issuer+subject, unlink recorded not deleted | **Schema only** (`003000050`), same probe run |
| Welcome letter documents (employee + contractor) | **Live** (code) / **Partial** not served — templates compiled in; program create prepends both as required `read` items. Trainee portal still Absent. Never Met. |
| Grading, testing, scores, thresholds, attempt history | **Live** (code) / **Partial** not served — `003000079` + heal + API + program-detail UI. Stored pass decision at attempt time. Acknowledgement is not a grade. Not an LMS. Never Met. |
| Domain layer, HTTP API, scheduler, UI for any of the above | **Partial** — programs, roster, attestations, reminders, scope, grading, welcome-letter auto-include, and binder `workforce_training` fill are Live in code; access gate, identity bindings, trainee portal remain schema-only / Absent |
| Binder section derived from live program state | **Live** (code) / **Partial** not served — `workforce_training` filled from assignment + intake ledgers at render; never Met |

**Applied to the lab database; still undelivered on the running binary.**
Migrations `003000047`–`003000050` are in `_sqlx_migrations` on lab. `003000079`
(grading) and `003000080` (supplier register) land in this change set with
server heal SQL so a tag bump is not required. Domain + API + thin UI are
**Live in code** for roster, attestations, reminders, scope writes, grading,
and the supplier register. They are **Partial** until served (running binary
stays `57715d1fc`; no `-AllowStaleOverwrite`). Access gate, identity bindings,
and the trainee portal remain schema-only / Absent.

Tables existing is **not** delivery. Do not read "the migration is applied" as
evidence that a capability is served.

---

## Suite observability (WEL + syslog)

Rule: [`suite-observability-wel-syslog.mdc`](../../.cursor/rules/suite-observability-wel-syslog.mdc)

Products in scope for both Windows Event Log (via `pim-windows-oplog`)
and an RFC 5424 syslog sink: AIC Server and service hosts; endpoint
agent; recording agent / evidence writers; Workspace Agent; database
management binaries and GUIs; shipping jump / session / recording proxy
capacity binaries; all shipping configurators (Win32 + Tauri) and
elevate helpers; every future shipping suite binary.

Internal libraries, one-shot build tools, and non-shipping examples are
out of scope unless packaged into a customer-facing EXE.

---

## Maintenance

When a status row changes, update it here in the same change set that
moves it. When a rule's **contract** changes, update the rule file.
Never move a forbidden construct, required pattern, required agent
behavior, or operator directive into this document — those belong in the
rule where the agent will actually read them.
