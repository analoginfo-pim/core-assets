# Tier 1 terminology glossary (provisional)

**Status:** Provisional — copied from
`docs/dev/localization-quality-audit-20260819.md` §4 (SHA `2a4eb94`).
A human PAM / security linguist must lock this before any claim of Live
terminology consistency.

**Rule after lock:** one approved rendering per EN term per tag. Agents must
not invent a second synonym.

| EN (source) | de | fr | es | zh-Hans | zh-TW | en-GB | Notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| session | Sitzung | session | sesión | 会话 | **工作階段** (lock one; forbid mix with 會話) | session | zh-TW must pick one |
| credential(s) | Zugangsdaten | identifiants | credenciales | 凭据 | 憑證 | credentials | Avoid Anmeldedaten unless login-specific |
| vault | Tresor | coffre-fort | bóveda | 保险库 | 保險庫 | vault | “Vault” only if branded product name |
| rotation | Rotation / Kennwortrotation | rotation | rotación | 轮换 | 輪替 | rotation | |
| elevation | Rechteausweitung | élévation de privilèges | elevación de privilegios | 提升 | 提升 | elevation | Prefer over bare “Elevation” loan |
| endpoint | Endpunkt | point de terminaison | extremo *(lock)* | 端点 | 端點 | endpoint | Avoid weak “punto final” |
| enclave | Enklave | enclave | enclave | 飞地 | 飛地 | enclave | DE: Enklave not Enclave |
| attestation | Attestierung | attestation | atestación | 证明 | 證明 | attestation | Not soft Bestätigung for workforce |
| recording (session) | Aufzeichnung | enregistrement | grabación | 录制 | 錄製 | recording | Not “registro” for replay |
| approval | Genehmigung | approbation | aprobación | 审批 | 核准 | approval | Lock vs Freigabe |
| jump host | Jump-Host *(or Sprunghost — lock)* | hôte de rebond | host de salto | 跳板主机 | 跳板主機 | jump host | |
| workstation | Arbeitsplatz | poste de travail | estación de trabajo | 工作站 | 工作站 | workstation | |
| Connect (button) | Verbinden | Connecter *(lock)* | Conectar | 连接 | 連線 | Connect | |
| Deny / Allow | Verweigert / Erlaubt | Refusé / Autorisé | Denegado / Permitido | 拒绝 / 允许 | 拒絕 / 允許 | Deny / Allow | EN must not keep German chips |
| healthy / unhealthy | ordnungsgemäß / gestört *(or lock ops pair)* | sain / non sain | correcto / incorrecto | 正常 / 异常 | 正常 / 異常 | healthy / unhealthy | EN chips today poisoned |

## Additional core vocabulary (provisional EN list)

Use consistently in English recovery and all target packs:

session, credential, vault, rotation, elevation, endpoint, enclave,
attestation, recording, approval, jump host, workstation, Connect, Open,
Launch, Deny, Allow, principal, roster, scope basis, welcome letter,
assessment binder, command governance, live session, My Workstations,
password recovery, SoftHSM (DNT), keyring, Universal Envelope, Admin Token
(break-glass — careful register).

## Process

1. Slice 1 cleans US English (no reverse-MT from `de`).
2. Human locks this table → rename status to **Locked** and date the
   revision.
3. Fan-out agents bind to the locked table only.
