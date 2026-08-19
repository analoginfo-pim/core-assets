import json
from pathlib import Path


def dig(o, p):
    n = o
    for x in p.split("."):
        if not isinstance(n, dict) or x not in n:
            return None
        n = n[x]
    return n


def find_key(tag, key):
    base = Path(rf"c:\analog-pim\core-assets\content\locales-ui\{tag}")
    hits = []
    for f in base.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        node = dig(d, key) if "." in key else d.get(key)
        if node is not None:
            text = node if isinstance(node, str) else node.get("text")
            hits.append((f.name, text))
    return hits


keys = [
    "technische_dokumentation",
    "general_settings",
    "tls_security",
    "server_control",
    "sectionLanding.desc.blocked_attacks",
    "technical.howTo.0",
    "ipScanner.emptyLoading",
]
for k in keys:
    print(k, "de=", find_key("de", k), "en=", find_key("en", k))
