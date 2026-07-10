#!/usr/bin/env python3
"""USCIS Case Status lookup — self-contained, stdlib-only (remote-ready).

Path A helper for the batman:case-status skill. Performs the USCIS OAuth 2.0
client-credentials flow, caches the bearer token (~30 min), and fetches
GET /case-status/{receipt} for one or more receipt numbers.

No third-party dependencies — uses only urllib/json/os so it runs in any remote
Claude Code container. If credentials are not set, it exits non-zero with a clear
message so the skill falls back to Path B (the public egov.uscis.gov portal).

Environment:
  USCIS_CLIENT_ID      (required)  OAuth client id from the firm's Developer Team App
  USCIS_CLIENT_SECRET  (required)  OAuth client secret
  USCIS_OAUTH_URL      (optional)  token endpoint; default = sandbox
  USCIS_API_BASE       (optional)  API base; default = sandbox

Defaults target the USCIS **sandbox** (api-int.uscis.gov). For production, set
USCIS_OAUTH_URL and USCIS_API_BASE to the prod URLs USCIS issues after the demo.

Usage:
  uscis_case_status.py RECEIPT [RECEIPT ...]
  uscis_case_status.py --json RECEIPT [RECEIPT ...]   # machine-readable output
  uscis_case_status.py --help
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

SANDBOX_OAUTH = "https://api-int.uscis.gov/oauth/accesstoken"
SANDBOX_API = "https://api-int.uscis.gov/case-status"

RECEIPT_RE = re.compile(r"^(IOE|EAC|WAC|LIN|SRC|MSC|NBC|YSC|NSC|VSC|TSC)[0-9]{10}$")

# token cache in the scratch/tmp dir so repeated calls within ~30 min reuse it
_TOKEN_CACHE = os.path.join(
    os.environ.get("TMPDIR", "/tmp"), ".uscis_token_cache.json"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def _load_cached_token() -> str | None:
    try:
        with open(_TOKEN_CACHE) as fh:
            data = json.load(fh)
        if data.get("expires_at", 0) > time.time() + 30:
            return data.get("access_token")
    except (OSError, ValueError):
        pass
    return None


def _save_cached_token(token: str, expires_in: int) -> None:
    try:
        with open(_TOKEN_CACHE, "w") as fh:
            json.dump(
                {"access_token": token, "expires_at": time.time() + expires_in},
                fh,
            )
        os.chmod(_TOKEN_CACHE, 0o600)
    except OSError:
        pass  # cache is best-effort; a failure just means we re-auth next time


def get_token() -> str:
    cached = _load_cached_token()
    if cached:
        return cached

    client_id = os.environ.get("USCIS_CLIENT_ID")
    client_secret = os.environ.get("USCIS_CLIENT_SECRET")
    if not client_id or not client_secret:
        _die(
            "credentials not set: export USCIS_CLIENT_ID and USCIS_CLIENT_SECRET "
            "(firm Developer Team App). Falling back to Path B (public portal).",
            code=3,
        )

    oauth_url = os.environ.get("USCIS_OAUTH_URL", SANDBOX_OAUTH)
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = urllib.request.Request(
        oauth_url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
    except Exception as exc:  # noqa: BLE001 - report any auth failure plainly
        _die(f"OAuth token request failed: {exc}", code=4)

    token = payload.get("access_token")
    if not token:
        _die(f"no access_token in OAuth response: {payload}", code=4)
    _save_cached_token(token, int(payload.get("expires_in", 1800)))
    return token


def fetch_status(receipt: str, token: str) -> dict:
    api_base = os.environ.get("USCIS_API_BASE", SANDBOX_API).rstrip("/")
    url = f"{api_base}/{urllib.parse.quote(receipt)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main(argv: list[str]) -> int:
    args = [a for a in argv if a not in ("--json",)]
    as_json = "--json" in argv
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    bad = [r for r in args if not RECEIPT_RE.match(r.upper())]
    if bad:
        _die(
            "invalid receipt number(s): "
            + ", ".join(bad)
            + " — expected 3 service-center letters + 10 digits (PII: verify before querying)."
        )

    token = get_token()
    results = []
    for receipt in args:
        receipt = receipt.upper()
        try:
            data = fetch_status(receipt, token)
            case = data.get("case_status", data)
            results.append(
                {
                    "receipt": receipt,
                    "form": case.get("formType") or case.get("form_type"),
                    "status": case.get("current_case_status_text_en")
                    or case.get("status"),
                    "detail": case.get("current_case_status_desc_en"),
                    "source": "API",
                }
            )
        except Exception as exc:  # noqa: BLE001 - never fabricate a status
            results.append(
                {"receipt": receipt, "error": str(exc), "source": "API"}
            )

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            if "error" in r:
                print(f"{r['receipt']} | LOOKUP FAILED | {r['error']} | source=API")
            else:
                print(
                    f"{r['receipt']} | {r.get('form') or '-'} | "
                    f"{r.get('status') or '-'} | source=API"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
