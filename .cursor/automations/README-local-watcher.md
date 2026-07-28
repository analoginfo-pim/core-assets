# Stuck agent supervisor — local watcher (the path that works)

## Root cause: Cloud Automation cannot unstick local agents

Cursor Automations cron jobs run as **Cloud Agents on a remote VM**. That
host does **not** mount Phil's workstation paths:

`C:\Users\phil\.cursor\projects\c-analog-pim\agent-transcripts`

So even a perfectly Saved + Enabled **"Stuck agent supervisor"** automation:

1. Cannot see local transcripts (scan path does not exist in the cloud).
2. Cannot `Task` interrupt into local Multitask parent chats.
3. At best writes a status note in a cloud chat Phil rarely watches.

Additional history on this machine:

| State | Evidence |
| --- | --- |
| Draft / prefill | `stuck-agent-supervisor-prefill.json` + `open_automation` handoff |
| Save failures | Operator: "no script"; UI: "Enter instructions for the agent before saving." |
| Enabled? | **No** — no Windows Scheduled Task, no reliable Automations run history locally |
| Cloud-vs-local | Binding repo `analoginfo-pim/core-assets` is only a checkout host — not the scan filesystem |

Parent duty in Multitask remains mandatory
(`.cursor/rules/stuck-agent-supervisor.mdc`). The local watcher is the
optional always-on complement that can actually see transcripts.

## What this local watcher does

| Piece | Role |
| --- | --- |
| `Scan-StuckAgents.ps1` | Scans local transcripts; writes `local-watcher-state/latest-report.md` + JSON |
| Interrupt queue | One markdown request per newly stuck ID under `local-watcher-state/interrupt-queue/` |
| `Install-StuckAgentLocalWatcher.ps1` | Registers Windows Scheduled Task `AIC-StuckAgentLocalWatcher` |

It does **not** auto-spawn Opus workers or explore fan-out. It queues a
**single** stop-planning interrupt request for the owning parent to execute
with `Task` + `interrupt: true` (AUTO only).

## Exact steps for Phil (Enable)

1. Open PowerShell on this workstation (BEAVIS2 / operator desktop).
2. Install and run once:

```powershell
cd C:\analog-pim\.cursor\automations
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-StuckAgentLocalWatcher.ps1 -IntervalMinutes 5 -RunOnceNow
```

3. Confirm the task exists and is Ready:

```powershell
Get-ScheduledTask -TaskName AIC-StuckAgentLocalWatcher | Format-List TaskName, State
Get-Content C:\analog-pim\.cursor\automations\local-watcher-state\latest-report.md
```

4. When the report lists live stuck IDs, open the owning **parent** Multitask
   chat and interrupt once using the text in the matching
   `local-watcher-state\interrupt-queue\<parent>__<agent>.md` file.

5. Optional: leave the Cursor Automation **"Stuck agent supervisor"** Disabled
   (or delete it). It cannot fix local planning stalls. Prefer this local
   watcher.

### Uninstall

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\analog-pim\.cursor\automations\Install-StuckAgentLocalWatcher.ps1 -Uninstall
```

## Manual one-shot scan (no task)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\analog-pim\.cursor\automations\Scan-StuckAgents.ps1
```

Exit codes: `0` = no live stuck, `1` = live stuck found, `2` = transcript root missing.

## Stop-planning interrupt text (for parents)

```text
STOP PLANNING. Deliver NOW from what you already know.
Return a short DONE checklist (done / deferred / blocked) for THIS slice only.
No more exploration, no more Read/Grep loops, no more planning.
If you lack facts, mark blocked with the one smallest missing path — then stop.
```
