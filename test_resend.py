#!/usr/bin/env python3
"""
Standalone test: sends one email via Resend to confirm your API key,
from-address, and to-address are all working. Run it locally:

    RESEND_API_KEY=... FROM_EMAIL=... NOTIFY_EMAIL=... python test_resend.py

Or set the three env vars in your shell/profile first, then just run it.
"""

import json
import os
import sys
from urllib import request, error


def main() -> int:
    resend_api_key = os.environ["RESEND_API_KEY"]
    from_email = os.environ["FROM_EMAIL"]
    to_email = os.environ["NOTIFY_EMAIL"]

    payload = json.dumps(
        {
            "from": from_email,
            "to": [to_email],
            "subject": "Resend test - Steam presence notifier",
            "html": "<p>If you're reading this, Resend is wired up correctly.</p>",
        }
    ).encode()

    req = request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Resend sits behind Cloudflare, which blocks the default
            # Python-urllib User-Agent outright (Cloudflare error 1010).
            # A normal-looking UA gets past that check.
            "User-Agent": "Mozilla/5.0 (compatible; steam-presence-notifier/1.0)",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode())
            print("Success:", result)
            return 0
    except error.HTTPError as e:
        print(f"Failed: HTTP {e.code}")
        print(e.read().decode())
        return 1


if __name__ == "__main__":
    sys.exit(main())