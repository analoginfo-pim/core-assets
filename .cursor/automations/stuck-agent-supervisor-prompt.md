# Stuck agent supervisor — Automations Instructions (paste if empty)

> **WARNING:** Cursor Automations cron is a Cloud Agent and cannot see
> `C:\Users\phil\.cursor\projects\...\agent-transcripts`.
> Enable the local watcher instead — see `README-local-watcher.md`.

Cron: `*/15 * * * *` (Cloud — ineffective for local Multitask)
Automations host repo binding (not scan scope): `analoginfo-pim/core-assets` @ `main`
Scan scope (local host only): `C:\Users\phil\.cursor\projects\c-analog-pim\agent-transcripts`

## Prefill key (for agents / open_automation)

The Glass Automations UI Instructions field maps to:

- Canonical: `workflow.prompts: [{ "prompt": "<text>" }]`  (**not** `text`)
- Prefer local watcher over enabling this Cloud Automation.

Paste body from `stuck-agent-supervisor-prompt-body.txt` only if you still want a Cloud reminder agent.
