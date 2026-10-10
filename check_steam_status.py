#!/usr/bin/env python3
"""
Polls the Steam Web API for a friend's presence status and emails (via Resend)
whenever that status changes. Designed to run on a schedule (e.g. GitHub
Actions cron) with the last-known state persisted in state.json in this repo.

Required environment variables:
  STEAM_API_KEY   - Steam Web API key (steamcommunity.com/dev/apikey)
  STEAM_ID        - Friend's SteamID64 (17-digit number)
  RESEND_API_KEY  - Resend API key (resend.com)
  NOTIFY_EMAIL    - Where to send the notification
  FROM_EMAIL      - Verified "from" address on Resend
                     (use "onboarding@resend.dev" if you have no verified domain)
"""

import json
import os
import sys
from pathlib import Path
from urllib import request, error

STATE_FILE = Path(__file__).parent / "state.json"

# Steam's personastate codes
PERSONA_STATES = {
    0: "Offline",
    1: "Online",
    2: "Busy",
    3: "Away",
    4: "Snooze",
    5: "Looking to trade",
    6: "Looking to play",
}


DEFAULT_UA = "Mozilla/5.0 (compatible; steam-presence-notifier/1.0)"


def http_json(url: str, method: str = "GET", headers: dict | None = None, body: bytes | None = None) -> dict:
    headers = dict(headers or {})
    headers.setdefault("User-Agent", DEFAULT_UA)
    req = request.Request(url, data=body, headers=headers, method=method)
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def get_player_summary(api_key: str, steam_id: str) -> dict:
    url = (
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        f"?key={api_key}&steamids={steam_id}"
    )
    data = http_json(url)
    players = data.get("response", {}).get("players", [])
    if not players:
        raise RuntimeError(
            "Steam API returned no player data. Check the SteamID64 and that "
            "the profile isn't fully private."
        )
    return players[0]


def load_last_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def send_email(resend_api_key: str, from_email: str, to_email: str, subject: str, html: str) -> None:
    url = "https://api.resend.com/emails"
    payload = json.dumps(
        {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
    ).encode()
    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json",
    }
    try:
        http_json(url, method="POST", headers=headers, body=payload)
    except error.HTTPError as e:
        raise RuntimeError(f"Resend send failed: {e.code} {e.read().decode()}") from e


def main() -> int:
    steam_api_key = os.environ["STEAM_API_KEY"]
    steam_id = os.environ["STEAM_ID"]
    resend_api_key = os.environ["RESEND_API_KEY"]
    notify_email = os.environ["NOTIFY_EMAIL"]
    from_email = os.environ["FROM_EMAIL"]

    player = get_player_summary(steam_api_key, steam_id)
    persona_name = player.get("personaname", "Your friend")
    state_code = player.get("personastate", 0)
    game_extra_info = player.get("gameextrainfo")  # present if currently in-game
    status_text = PERSONA_STATES.get(state_code, f"Unknown ({state_code})")

    last_state = load_last_state()
    last_status_text = last_state.get("status_text")
    last_game = last_state.get("game")

    changed = (status_text != last_status_text) or (game_extra_info != last_game)

    if changed:
        if last_status_text is None:
            print(f"First run. Current status: {status_text}. Not sending email, just recording baseline.")
        else:
            lines = [f"{persona_name}'s status changed:", f"{last_status_text} -> {status_text}"]
            if game_extra_info:
                lines.append(f"Now playing: {game_extra_info}")
            elif last_game and not game_extra_info:
                lines.append(f"Stopped playing: {last_game}")
            body_html = "<br>".join(lines)
            subject = f"{persona_name} is now {status_text}"
            send_email(resend_api_key, from_email, notify_email, subject, body_html)
            print(f"Status changed ({last_status_text} -> {status_text}). Email sent.")
    else:
        print(f"No change. Status still {status_text}.")

    save_state(
        {
            "status_text": status_text,
            "game": game_extra_info,
            "persona_name": persona_name,
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())