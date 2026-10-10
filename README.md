# Steam Presence Notifier

Polls a friend's Steam presence status every 5 minutes via GitHub Actions and
emails you (via Resend) whenever it changes (Offline -> Online, started/stopped
playing a game, etc.).

## Setup

1. **Create a new GitHub repo** and push these files to it (can be private).

2. **Add repo secrets** (Settings -> Secrets and variables -> Actions -> New repository secret):
   - `STEAM_API_KEY` - your Steam Web API key
   - `STEAM_ID` - your friend's SteamID64 (17-digit number)
   - `RESEND_API_KEY` - your Resend API key
   - `NOTIFY_EMAIL` - the email address to notify (you)
   - `FROM_EMAIL` - the verified "from" address on Resend
     (use `onboarding@resend.dev` if you don't have a verified sending domain,
     but note Resend's shared test domain can only send to the email address
     on your own Resend account)

3. That's it. The workflow in `.github/workflows/steam-presence.yml` runs on a
   5-minute cron automatically. The first run just records a baseline status
   (no email sent); every run after that emails you only when something changed.

4. You can also trigger a run manually any time from the repo's **Actions** tab
   (the `workflow_dispatch` trigger) to test it immediately rather than waiting
   for the next scheduled tick.

## Notes

- Steam's API has no push/webhook mechanism, so polling is required. 5 minutes
  is a safe interval; going much faster isn't really useful since Steam itself
  doesn't update presence in real time either.
- If your friend's profile/game details are set to private, `personastate`
  may not be reliable or may always show as Offline regardless of truth.
- State is tracked in `state.json`, committed back to the repo by the workflow
  itself after every run, so changes are detected across runs.
- To track multiple friends, duplicate the SteamID secret handling and extend
  the script, or just run multiple copies of this repo.
