# Workspace always-apply Cursor rules (tracked mirror)

**Live location** (what agents load): `c:\analog-pim\.cursor\rules`

**This directory** is the **tracked mirror** in `core-assets` for versioning
and recovery. `c:\analog-pim` itself is not a git repository (multi-repo
container), so the live rules tree is not versioned unless mirrored here.

**Sync direction:** workspace → `core-assets` only. Never copy the other way
without deliberate intent (for example a recovery restore).

If you edit a rule under the live workspace path, mirror the same file into
this directory in the same change set. An edit that stays only on one disk
is not recoverable from git.
