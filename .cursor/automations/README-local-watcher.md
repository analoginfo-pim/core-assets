# Stuck agent supervisor — local Hidden watcher (multi-signal)

## Slack notifications (unrelated to stuck-scan)

Agents notify Phil/Robert via Incoming Webhooks when Slack MCP is missing.
See `../rules/slack-webhook-agent-access.mdc` and `Send-AgentSlack.ps1`.
Webhook URLs live only in `../secrets/slack-webhooks.json` (gitignored).

The watcher itself Slacks Phil **only when a new live-stuck ID is queued**
— not on every tick, not for UI ghosts.

## Why the old watcher was worthless

`mtime` / last-jsonl-write idle is a weak signal:

- Cursor can sit on **Planning next moves** with **no new jsonl lines**
  (prompt-only forever). The file never contains the string
  `planning next moves`, so a string match misses it.
- Cursor can keep writing **thinking / status** so mtime stays fresh
  while **no tool** runs (tool-starvation).
- Finished agents with `turn_ended`/`success` still show Running in
  Multitask (UI ghosts). Listing them as live-stuck caused false
  interrupts; ignoring them without a parent signal left Phil blind.
- Tightening idle 15m → 4m did not fix detection.

## Strategies adopted (sourced — not "best practice" without a link)

| # | Strategy | From | What we implemented |
| --- | --- | --- | --- |
| 1 | **Dead-man lease + isolated supervisor** | [Crontap / Healthchecks.io dead-man](https://crontap.com/blog/dead-man-switch-explained-for-developers); [OpenClaw isolated heartbeat](https://buttergrow.com/blog/isolated-session-heartbeat-monitoring); [Antigravity monotonic `step_idx`](https://antigravitylab.net/en/articles/agents/antigravity-long-running-agent-supervision-architecture) | Cursor hooks (`preToolUse`, `postToolUse`, `afterAgentThought`, `subagentStart`, `stop`, …) write `local-watcher-state/leases/<id>.json`. Thought-only bumps `thought_idx`, **not** `progress_idx`. The Hidden scheduled task is the isolated reader. |
| 2 | **Stuck-tool / tool-starvation / zero-tool planning stall** | [ClawGuard `stuck-tool` + `loop`](https://github.com/clawnify/clawguard); Antigravity (timestamp-only heartbeat is insufficient — need progress vs stage) | Parse jsonl for last **tool_use** vs last **thinking/text** vs `turn_ended`. Prompt-only forever = 0 tools + age > ~3.5 min → live-stuck. Last event `tool_use` with no result + idle → stuck-tool. Thinking-only while `tool_count` unchanged across ticks → tool-starvation. |
| 3 | **Hung helper CPU** | OpenClaw: in-process heartbeat dies with the hang | Sample Cursor/node CPU across ticks. 0-CPU helpers (not the main UI) go in the report with PID + name. **Never** auto-killed. |

Cursor Cloud Automations still cannot see
`C:\Users\phil\.cursor\projects\c-analog-pim\agent-transcripts`.
Do not rely on Cloud for unstick.

## What this local watcher does

| Piece | Role |
| --- | --- |
| `../hooks/Write-AgentHeartbeat.ps1` + `../hooks.json` | Cursor hook: renew lease. Fail-open, Hidden, never deny. Also copied to `%USERPROFILE%\.cursor\hooks`. |
| `Scan-StuckAgents.ps1` | Multi-signal scan; writes `latest-report.md`, `PARENT-SIGNAL.md`, `status.json` |
| Interrupt queue | One markdown request per **newly** stuck ID under `local-watcher-state/interrupt-queue/` (deduped) |
| Slack | Only on **new** live-stuck IDs |
| `Install-StuckAgentLocalWatcher.ps1` | Registers `AIC-StuckAgentLocalWatcher` Hidden + installs user hooks |

It does **not** spawn Cursor agents, Opus workers, or explore fan-out. It
**queues** a single stop-planning interrupt request. The **owning Multitask
parent** must run `Task` + `interrupt: true` (AUTO only).

### Detection classes

| Class | Behavior |
| --- | --- |
| **Live stuck** | Planning stall (0 tools, age ≥ ~3.5 min), tool-starvation, stuck-tool pending, read/grep loop, or repeated-tool loop — **and** no `turn_ended`/success → interrupt queue |
| **UI ghost (completed)** | `turn_ended`/`success` on disk → report only; **never** interrupt-queued |
| **Hung helper** | Cursor/node PID with ~0 CPU over the idle window and no recent transcript write → report only |
| **Cold aborted** | Old aborted / missing turn_ended beyond live window → report only |

Never-interrupt prefixes (hard-coded, do not queue): `5516df5e`,
`873476da`, `e766aa3a`, `8e2dd3b8`.

## How a parent consumes the queue

1. At the start of a Multitask parent turn (or after sleep), **read**
   `local-watcher-state/PARENT-SIGNAL.md` first. That file is the
   parent-visible signal (no window, no toast).
2. If **Live stuck** is 0: still do your own child status-check (watcher
   is complement, not substitute).
3. For each **Interrupt now** id: `Task` with `resume: <id>`,
   `interrupt: true`, omit model (AUTO). Prompt = the stop-planning
   text in `interrupt-queue\<parent>__<id>.md`.
4. One interrupt per id per incident. If it does not deliver, abandon.
   Do not interrupt ghosts.

## Exact steps for Phil (Enable)

```powershell
cd C:\analog-pim\.cursor\automations
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-StuckAgentLocalWatcher.ps1 -IntervalMinutes 3 -RunOnceNow
```

`-RunOnceNow` uses `Start-Process -WindowStyle Hidden`.

Confirm Hidden + report:

```powershell
Get-ScheduledTask -TaskName AIC-StuckAgentLocalWatcher | Format-List TaskName, State
schtasks /Query /TN AIC-StuckAgentLocalWatcher /V /FO LIST | Select-String -Pattern 'Task To Run|Last Run|Status|Hidden'
Get-Content C:\analog-pim\.cursor\automations\local-watcher-state\PARENT-SIGNAL.md
Get-Content C:\analog-pim\.cursor\automations\local-watcher-state\latest-report.md -Head 40
```

### Uninstall

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\analog-pim\.cursor\automations\Install-StuckAgentLocalWatcher.ps1 -Uninstall
```

User hooks under `%USERPROFILE%\.cursor\hooks` are left in place (fail-open;
they only write lease files).

## Manual one-shot scan (Hidden, no task)

```powershell
Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -ArgumentList '-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File C:\analog-pim\.cursor\automations\Scan-StuckAgents.ps1' `
  -WindowStyle Hidden -Wait
```

Exit codes: `0` = no live stuck, `1` = live stuck found, `2` = transcript root missing.

## Focus / host-session safety

- Scheduled Task action: `powershell.exe -WindowStyle Hidden ...`
- Task settings: `-Hidden`
- `-RunOnceNow`: `Start-Process -WindowStyle Hidden`
- Hook command: `powershell.exe -WindowStyle Hidden ...`
- **Never** Normal/Maximized, never Activate/BringToFront
- Notifications = `PARENT-SIGNAL.md` + optional Slack on **new** live-stuck

## Stop-planning interrupt text (for parents)

```text
STOP PLANNING. Deliver NOW from what you already know.
Return a short DONE checklist (done / deferred / blocked) for THIS slice only.
No more exploration, no more Read/Grep loops, no more planning.
If you lack facts, mark blocked with the one smallest missing path — then stop.
```

## Durable copy

Workspace `.cursor` is not a git root. Scripts, hooks, and the rule are
mirrored under `core-assets/.cursor/` so they are not machine-only.
