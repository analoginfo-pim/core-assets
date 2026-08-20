# Do-not-translate list (Tier 1 retranslation)

**Authority:** product trademarks, protocol names, control identifiers, SPDX,
placeholder tokens, and technical literals. Translating these is a defect.

Agents and linguists MUST leave these substrings unchanged (including case),
except where the glossary explicitly marks a localized product-chrome form
(e.g. button label “Connect” may become Verbinden / Conectar — that is
**chrome**, not the protocol name).

## Product and brand

| Literal | Notes |
| --- | --- |
| AIC | Company / product brand |
| AIC Server | Product name |
| PAM / PIM / PUM | Product domain acronyms (keep Latin) |
| CMMC | Framework name |
| NIST / SP 800-53 / SP 800-171 / SP 800-172 | Authority short names |
| FedRAMP / FIPS / CMVP | Keep Latin |
| SoftHSM / PKCS#11 | Keep Latin |
| Open Source Credits | Page title may localize chrome; SPDX bodies stay English |

## Protocols and standards (never translate)

SSH, RDP, VNC, TLS, SAML, Kerberos, LDAP, OAuth, OIDC, RADIUS, Syslog,
Modbus, OPC-UA, OPC UA, DNP3, S7, IEC 62443, NERC CIP, GDPR, LGPD, ISO 27001
(control ids only — do not paste licensed ISO body text).

## Control identifiers

Pattern: `AC-1`, `AC-2(1)`, `SC-13`, `AU-9`, `IA-5`, etc.
Always render as `{id} — {localized short title}` where the product already
does; the **id** stays Latin.

## SPDX / license identifiers

`MIT`, `Apache-2.0`, `BSD-3-Clause`, `GPL-3.0-only`, etc. — never translate.

## Placeholder / interpolation tokens

Leave exact spelling:

- `{{name}}`, `{{count}}`, `{{username}}`, `{{session_id}}`, `{{resource}}`
- `{{security_contact_name}}`, `{{plural}}` (until plural redesign)
- Any `__PH0__`-style token if introduced by tooling

## Technical / UI literals often identical on purpose

HTTP method names in docs (`GET`, `POST`), status codes (`401`, `403`, `429`),
MIME types, file extensions (`.json`, `.msi`), IANA time zone ids
(`America/Los_Angeles`), BCP-47 tags (`zh-Hans`, `en-GB`), UUID examples.

## Buttons vs product verbs

| English chrome | May localize? | Keep Latin when |
| --- | --- | --- |
| Connect (button) | Yes (glossary) | Referring to product feature name in mixed UI |
| Jump / Jump host | Prefer glossary form; “Jump” alone often stays | Product “Jump” capacity brand |
| Vault | Translate as product concept (Tresor / …) | Branded “Vault” product title if any |
| Deny / Allow | Yes | — |

## Quarantine reminder

If an English source string still contains German (`autorisiert`, `gesund`,
`oeffnet`, …), **do not translate it**. Flag for Slice 1 English recovery.
