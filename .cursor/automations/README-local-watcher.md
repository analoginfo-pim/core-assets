# Stuck agent supervisor — local Hidden watcher (the path that works)

## Slack notifications (unrelated to stuck-scan)

Agents notify Phil/Robert via Incoming Webhooks when Slack MCP is missing.
See `../rules/slack-webhook-agent-access.mdc` and `Send-AgentSlack.ps1`.
Webhook URLs live only in `../secrets/slack-webhooks.json` (gitignored).

## Root cause: Cloud Automation cannot unstick local agents

Cursor Automations cron jobs run as **Cloud Agents on a remote VM**. That
host does **not** mount Phil's workstation paths:

`C:\Users\phil\.cursor\projects\c-analog-pim\agent-transcripts`

So even a perfectly Saved + Enabled **"Stuck agent supervisor"** automation:

1. Cannot see local transcripts (scan path does not exist in the cloud).
2. Cannot `Task` interrupt into local Multitask parent chats.
3. At best writes a status note in a cloud chat Phil rarely watches.

**Do not rely on Cloud for unstick.** Parent duty in Multitask remains
mandatory (`.cursor/rules/stuck-agent-supervisor.mdc`). The local **Hidden**
Scheduled Task is the always-on backup that can actually see transcripts.

## What this local watcher does

| Piece | Role |
| --- | --- |
| `Scan-StuckAgents.ps1` | Scans local transcripts (parents + `*/subagents/*.jsonl`); writes `local-watcher-state/latest-report.md` + JSON |
| Interrupt queue | One markdown request per **newly** stuck ID under `local-watcher-state/interrupt-queue/` (deduped) |
| `Install-StuckAgentLocalWatcher.ps1` | Registers Windows Scheduled Task `AIC-StuckAgentLocalWatcher` with **Hidden** PowerShell (no focus steal) |

It does **not** spawn Cursor agents, Opus workers, or explore fan-out. It
**queues** a single stop-planning interrupt request. The **owning Multitask
parent** must run `Task` + `interrupt: true` (AUTO only).

### Detection (aligned with the rule)

| Class | Behavior |
| --- | --- |
| **Live stuck** | Idle ≥ **~4 min** (default; rule band 3–5), **no** `turn_ended`/success; planning with no tools, Read/Grep loops, mid-tool hang, or no transcript growth across ticks → interrupt queue |
| **UI ghost (completed)** | `turn_ended`/`success` on disk in the last N hours (default 6) → listed in report only; **never** interrupt-queued (Multitask may still show Running) |
| **Cold aborted** | Old aborted / missing turn_ended beyond live window → report only |

## Exact steps for Phil (Enable)

1. Open PowerShell on this workstation (operator desktop). A one-shot install
   console is fine; the **task itself** runs Hidden thereafter.
2. Install and run once Hidden:

```powershell
cd C:\analog-pim\.cursor\automations
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-StuckAgentLocalWatcher.ps1 -IntervalMinutes 5 -RunOnceNow
```

`-RunOnceNow` uses `Start-Process -WindowStyle Hidden` — no window on top of
your work.

3. Confirm the task exists, is Ready, and the action includes Hidden:

```powershell
Get-ScheduledTask -TaskName AIC-StuckAgentLocalWatcher | Format-List TaskName, State
schtasks /Query /TN AIC-StuckAgentLocalWatcher /V /FO LIST | Select-String -Pattern 'Task To Run|Last Run|Status|Hidden'
Get-Content C:\analog-pim\.cursor\automations\local-watcher-state\latest-report.md -Head 20
```

4. When the report lists **Live stuck** IDs, open the owning **parent** Multitask
   chat and interrupt once using the text in
   `local-watcher-state\interrupt-queue\<parent>__<agent>.md`.

5. Optional: leave the Cursor Automation **"Stuck agent supervisor"** Disabled
   (or delete it). Prefer this local Hidden watcher.

### Uninstall

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\analog-pim\.cursor\automations\Install-StuckAgentLocalWatcher.ps1 -Uninstall
```

## Manual one-shot scan (Hidden, no task)

```powershell
Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -ArgumentList '-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File C:\analog-pim\.cursor\automations\Scan-StuckAgents.ps1' `
  -WindowStyle Hidden -Wait
```

Or (if you accept a console for debugging):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\analog-pim\.cursor\automations\Scan-StuckAgents.ps1
```

Exit codes: `0` = no live stuck, `1` = live stuck found, `2` = transcript root missing.

## Focus / host-session safety

- Scheduled Task action: `powershell.exe -WindowStyle Hidden ...`
- Task settings: `-Hidden`
- `-RunOnceNow`: `Start-Process -WindowStyle Hidden`
- **Never** Normal/Maximized, never Activate/BringToFront
- Notifications = file under `local-watcher-state\` (and optional Slack) — not a toast window

## Stop-planning interrupt text (for parents)

```text
STOP PLANNING. Deliver NOW from what you already know.
Return a short DONE checklist (done / deferred / blocked) for THIS slice only.
No more exploration, no more Read/Grep loops, no more planning.
If you lack facts, mark blocked with the one smallest missing path — then stop.
```

## Durable copy

Workspace `.cursor` is not a git root. Scripts are mirrored under
`core-assets/.cursor/automations/` so they are not machine-only.
