# Parent handoff — stuck-agent scan (2026-07-27)

Owning Multitask parent: `f5ae3f61-8d47-4344-85d2-207855496616`

## Live stuck right now

**None** (local scan of 74 parents / 275 subagents). No Task interrupt needed from this tree.

## Cold aborted / UI ghosts (do NOT re-interrupt)

| agent_id | parent_path | last write age | stuck reason | action |
| --- | --- | ---: | --- | --- |
| `3e4f4c6d-de19-4bde-828a-d5debb0e419f` (Check serializer sibling) | `baeef5eb-d02e-4cb3-946c-84ebed3fdb13` | ~21 h | already aborted after stop-planning | Abandon; finish serializer slice in parent or one AUTO replacement if still needed |
| `c5a61a21-973e-4460-8270-59b252bfff7c` | `baeef5eb-d02e-4cb3-946c-84ebed3fdb13` | ~21 h | already_aborted_cold | Abandon |
| `ffab5009-fc2a-4ffb-85b7-1d65c8e03678` | `baeef5eb-d02e-4cb3-946c-84ebed3fdb13` | ~21 h | already_aborted_cold | Abandon |
| `d256079f-0b3e-45f9-a33b-0f431759a051` | `18e6f253-1ea4-4d60-aa80-cc02a7a6722c` | ~22 h | already_aborted_cold | Abandon |
| older IDs under `97f3726b…` / `e3f6ec19…` | (foreign parents) | days | already_aborted_cold | Report only — foreign parent must abandon |

## Interrupt text (if a LIVE stuck appears)

```text
STOP PLANNING. Deliver NOW from what you already know.
Return a short DONE checklist (done / deferred / blocked) for THIS slice only.
No more exploration, no more Read/Grep loops, no more planning.
If you lack facts, mark blocked with the one smallest missing path — then stop.
```

## Enable local watcher (already registered this run)

Task `AIC-StuckAgentLocalWatcher` is **Ready** (every 5 minutes).
Reports: `C:\analog-pim\.cursor\automations\local-watcher-state\latest-report.md`
