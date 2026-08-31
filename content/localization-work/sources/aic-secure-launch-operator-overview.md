# AIC Secure Launch — operator overview (English source)

## What it is

AIC Secure Launch is a Windows (also Linux/macOS) helper installed next to
the console. You sign in to AIC Server, pick an authorized published
application, and the helper starts it with the vaulted credential. You
do not type the application password.

## What it is not

These local launches are **not** session-recorded. They are not a
Privileged Access Management (PAM) Connect recording. Do not treat a
helper launch as Met or certified evidence of recorded access.

## Sign-in

1. Local account (lab-dev may show a sample-account list).
2. Active AIC Server session token after browser sign-in.
3. Domain / alternate provider when configured: finish Domain on the
   AIC Server login page, then paste the session token into the helper.

Domain appears on `/login` only when Windows Negotiate and/or a ready
OpenID Connect provider is enabled. On-prem LDAP bind is not available
yet. Do not join the operator host to a domain solely to test this.

## Install (lab)

```text
powershell -NoProfile -ExecutionPolicy Bypass -File c:\analog-pim\pim-secure-launch\scripts\Deploy-AicSecureLaunchDev.ps1
```

Desktop shortcut uses the AIC icon from core-assets.
