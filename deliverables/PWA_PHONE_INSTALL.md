# Closing Agent — Phone install (PWA)

Install the dashboard as an app on iPhone or Android after this PR is **reviewed and merged** (and GitHub Pages has rebuilt).

**Live URL:** https://codesurfing10.github.io/Closing-Agent-Manufacturing-/docs/

> **Check-in before merge:** Please review the PR and confirm before merging. Do not merge until you have signed off.

## iPhone / iPad (Safari)

1. Open the live URL above in **Safari** (Chrome on iOS cannot Add to Home Screen the same way).
2. Tap the **Share** button (square with arrow).
3. Scroll and tap **Add to Home Screen**.
4. Confirm the name (**Closing Agent**) and tap **Add**.
5. Launch from the home screen — it opens standalone (no Safari chrome).

## Android (Chrome)

1. Open the live URL in **Chrome**.
2. Use the menu (⋮) → **Install app** / **Add to Home screen**, or tap the install banner if shown.
3. Confirm install. Launch from the home screen or app drawer.

## What works offline

- The **app shell** (HTML/CSS/JS/icons) is cached so the UI can load without network.
- **API calls** to `https://closing-agent-manufacturing.onrender.com` stay **network-first** — live data still requires connectivity. Offline API requests fail gracefully rather than serving stale API data.

## Notes

- First visit online is required so the service worker can cache the shell.
- After deploy, a hard refresh may be needed once for the new service worker to activate.
- Theme matches the dark dashboard (`#0d1117` / green accent).
