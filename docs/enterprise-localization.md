# Enterprise localization (central rule — all products)

**Audience:** AIC and Robert product lines. This is the localization
standard for every shipping security product in the suite.

**Canonical home:** `core-assets/docs/enterprise-localization.md`
(GitHub: `analoginfo-pim/core-assets`). Cursor agents also load
`.cursor/rules/enterprise-localization.mdc`.

**Related rules:** language tiers and must-localize artifact list in
`compliance-artifacts-must-localize.mdc`; catalogs ship in the installer
per `multilingual-tier-1-installer.mdc`.

---

You are performing enterprise-grade localization for a suite of security
products used in:

- Defense Industrial Base (DIB)
- Intelligence Community (IC)
- Operational Technology (OT) environments
- Enterprise IT (global)
- Critical infrastructure
- Regulated industries

The products include:

| Product | Status |
| --- | --- |
| PIM (Privileged Identity Management) | Shipping |
| PAM (Privileged Access Management) | Shipping |
| PUM (Privileged User Management) | Shipping |
| IGA (Identity Governance & Administration) | **Roadmap** — localize IGA strings when they exist; do not invent IGA features or terminology |
| Auditing / Session Recording (similar class: Venta, Balabit, Fudo, Teleport) | Shipping |
| Secure Remote Access | Shipping |
| Compliance & Reporting | Shipping |

Your job is to produce high-accuracy, domain-correct localization for
UI, workflows, alerts, logs, documentation, and compliance text.

Follow these rules exactly.

Workforce training and welcome letters are a **separate** surface: sixth-grade
plain language and original illustrations
(`training-materials-plain-language-and-images.mdc`). This document governs
operator, administrator, auditor, and product UI/compliance text.

Official regulation bodies stay in the language the authority published.
AIC chrome, mappings, notices, and summaries localize. Do **not** translate
or paste licensed ISO 27001 control text. Do **not** invent unofficial
CMMC / NIST 800-53 body translations and call them the control.

--------------------------------------------------
1. GENERAL RULES
--------------------------------------------------

## 1.1 Accuracy

- Use precise technical terminology for security, identity, OT protocols,
  and compliance.
- Never invent features or terminology.
- If a term is ambiguous, choose the most common enterprise security meaning.

## 1.2 Tone

- Professional
- Clear
- Neutral
- Suitable for regulated industries
- Avoid idioms, slang, or culturally specific phrasing.

## 1.3 No creativity

Localization must be literal, consistent, and domain-correct, not stylistic.

## 1.4 Preserve placeholders

Do not translate variables, tokens, or code-like elements, for example:
`{username}`, `{session_id}`, `{resource}`, SAML, Kerberos, LDAP, Modbus,
OPC-UA, DNP3.

## 1.5 Preserve capitalization rules

Follow capitalization conventions of the target language for:

- Buttons
- Menu items
- Alerts
- Headings
- Policy names

--------------------------------------------------
2. MODULE-LEVEL LOCALIZATION REQUIREMENTS
--------------------------------------------------

Translate all text according to the module’s domain.

## 2.1 PAM / PIM / PUM

Translate:

- Access request workflows
- Approval/denial messages
- Justification prompts
- Privilege elevation messages
- Password vault UI
- Rotation/checkout/heartbeat messages
- Session initiation/termination messages
- Policy editor text
- Role descriptions
- MFA prompts
- Credential lifecycle messages

## 2.2 IGA (roadmap)

When IGA surfaces exist, translate:

- Certification campaigns
- Access reviews
- Governance workflows
- Risk scoring text
- Policy descriptions
- Delegation workflows
- Identity lifecycle events
- Compliance mappings

Do not ship IGA copy for features that are not in the product.

## 2.3 Auditing / Session Recording

Translate:

- Session playback UI
- Timeline markers
- Event annotations
- Keystroke/command summaries
- Evidence export text
- Chain-of-custody messages
- Audit log metadata
- Alert descriptions
- Forensic workflow text

## 2.4 OT Security

Translate:

- Asset inventory fields
- OT protocol event descriptions (Modbus, S7, DNP3, OPC-UA)
- Network topology labels
- Operator alerts
- Remote access workflows
- Maintenance session messages
- Safety-critical warnings
- ICS/SCADA terminology

## 2.5 Compliance & Reporting

Translate AIC-authored:

- GDPR, LGPD, NERC CIP, IEC 62443, ISO 27001 **chrome, mappings, and summaries**
- Policy documentation
- Evidence summaries
- Risk assessment templates
- Legal notices
- Data retention text
- Privacy statements
- Audit report sections

Official control bodies and licensed ISO text: see the honesty paragraph
at the top of this document.

--------------------------------------------------
3. LANGUAGE-SPECIFIC RULES
--------------------------------------------------

Apply the following language rules when translating. Catalog tags match
`compliance-artifacts-must-localize.mdc` (Tier 1 mandatory: `en`, `en-GB`,
`de`, `fr`, `es`, `zh-Hans`, `zh-TW`). Hebrew (`he`) is Tier 2 (RTL).

**Language packs** live in `core-assets` (`content/locales/`,
`content/locales-ui/`, `content/i18n-native/`), tagged by product in
`content/language-packs/manifest.json`. Every leaf is
`{ "text", "source_sha256" }` (SHA-256 of UTF-8 NFC of the US English
`text`). Developer how-to:
[`language-pack-developer-standard.md`](language-pack-developer-standard.md).

**Picker:** when two or more packs are installed, show flag + display name +
BCP-47 tag (`en`, `zh-TW`, …). Hide the flag when only one pack is installed.
`en-GB` is not an alias of `en`. `zh-TW` is not a conversion of `zh-Hans`.

## 3.1 German (`de`)

- Use formal “Sie”.
- Compound nouns must be correct (e.g., “Sitzungsaufzeichnung”,
  “Rollenüberprüfung”).
- Avoid English loanwords unless industry-standard.

## 3.2 French (`fr`)

- Use formal “vous”.
- Follow ANSSI terminology for cybersecurity.
- Avoid anglicisms unless required (e.g., “session”, “audit”).

## 3.3 Spanish (`es`)

- Use neutral international Spanish.
- Avoid country-specific idioms.
- Use formal “usted”.

## 3.3a English (UK) (`en-GB`) — Tier 1

- Full translation from US English — not a spelling overlay and not an
  alias of `en`.
- UK spelling and legal phrasing where AIC authors the prose.
- Official CMMC / NIST bodies stay in the authority language (typically
  US-published English).

## 3.3b Chinese Simplified (`zh-Hans`) — Tier 1

- Mainland China; MLPS 2.0 vocabulary.
- Flag / country: CN. Never use the Taiwan flag for this pack.

## 3.3c Chinese (Taiwan) (`zh-TW`) — Tier 1

- Taiwan Traditional Chinese. Canonical tag is **`zh-TW`** (not `zh-Hant`
  as the folder name).
- Translate from US English. **Never** convert characters from `zh-Hans`
  and ship.
- Flag / country: TW. Never use the PRC flag for this pack.

## 3.3d Hebrew (`he`) — Tier 2

- Israel defense and regulated industries.
- Manifest `dir=rtl`. RTL layout is part of the pack.
- Flag / country: IL.

## 3.4 Japanese (`ja`) — Tier 2

- Use polite form (です/ます).
- Follow Japanese IT/security terminology conventions.
- Avoid katakana overuse.

## 3.5 Korean (`ko`) — Tier 2

- Use formal polite form.
- Follow Korean cybersecurity terminology standards.

## 3.6 Portuguese (Brazilian) (`pt-BR`) — Tier 2

- Use Brazilian Portuguese.
- Follow LGPD terminology.

## 3.7 Italian (`it`) — Tier 2

- Use formal “Lei”.
- Follow Italian cybersecurity terminology.

## 3.8 Polish (`pl`) — Tier 3

- Use formal register.
- Follow Polish industrial cybersecurity terminology.

## 3.9 Turkish (`tr`) — Tier 3

- Use formal register.
- Follow Turkish IT/security terminology.

## 3.10 Chinese (Simplified) (`zh-Hans`) — Tier 1

- Use Mainland China terminology.
- Follow MLPS 2.0 cybersecurity vocabulary.

## 3.11 English (UK) (`en-GB`) — Tier 1

- Use UK spelling and legal phrasing consistently (organisation, colour,
  authorise) in operator-facing UK filing text.
- Do not rewrite US English source identifiers (`en` remains the source
  catalog).

## 3.12 Other shipped or requested tags

Dutch (`nl`), Swedish (`sv`), Finnish (`fi`), Arabic MSA (`ar`): formal
register, industry terminology, no idioms. English is often accepted
alongside Arabic for Gulf industrial regulators.

--------------------------------------------------
4. OUTPUT FORMAT
--------------------------------------------------

When producing localized strings (translator / agent work product),
always output JSON. Catalogs in the product still land as locale JSON
files (`locales/<tag>/`, SPA `ui/src/i18n/locales/<tag>/`, or
`offline_localized_copy`) — this shape is the review packet, not a
replacement for those files.

For a single string:

```json
{
  "source_text": "...",
  "target_language": "French",
  "localized_text": "...",
  "notes": "Any clarifications or domain-specific decisions"
}
```

For multiple strings, output an array:

```json
[
  {
    "source_text": "...",
    "localized_text": "..."
  },
  {
    "source_text": "...",
    "localized_text": "..."
  }
]
```

Include `target_language` (or BCP-47 `tag`) on every object in a batch
when more than one language is in the same packet.

--------------------------------------------------
5. QUALITY CHECKS
--------------------------------------------------

Before finalizing, ensure:

- Terminology matches industry standards.
- No placeholders were translated.
- No hallucinated features.
- No informal tone.
- No culturally inappropriate phrasing.
- No ambiguous translations.
- No missing security context.
- No mistranslated OT protocol terms.
- No mistranslated compliance/legal text.
- IGA copy exists only for IGA surfaces that are actually in the product.
- Official / licensed control bodies were not rewritten as if they were
  AIC translations.

---

--------------------------------------------------
6. WORK QUEUE (new and changed source)
--------------------------------------------------

`core-assets` is the localization home. There is no separate localization
GitHub repository.

When Help, manuals, or other must-localize English source is **added or
changed**, record a work item in
`content/localization-work/` in the same change set. Translators read
`content/localization-work/queue.md`. The recorder is
`scripts/localization-work/localization_work.py` (Python 3, stdlib only).

Agent draft catalogs do **not** close an item. Close only when every
required tag has a reviewed catalog. Missing Tier 1 tags (`en-GB`,
`zh-Hans` today) keep the item open.

Do not add a git hook or a product environment variable for this queue.
Queue notes stay in product language.

See `content/localization-work/README.md` and the agent rule
`localization-work-queue.mdc`.

---

## Origin

2026-08-16 — operator: this markdown is the central localization rule
for all products; share with Robert. IGA is on the roadmap.

2026-08-17 — operator: record new and changed localization work in
`content/localization-work/` so translators see a durable to-do list.
