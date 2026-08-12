# Troubleshooting Guide

## App Won't Load or Shows a Blank Screen

1. Hard-refresh the page (Ctrl+Shift+R on Windows/Linux, Cmd+Shift+R on Mac) to clear a stale
   cached version of the app.
2. Try an incognito/private window. If it loads there, a browser extension (especially ad
   blockers or script blockers) is likely interfering — disable extensions one at a time to
   find the culprit.
3. Confirm the browser is up to date. We support the current and previous major version of
   Chrome, Firefox, Safari, and Edge; older browsers are not guaranteed to work.
4. If the issue persists across browsers and devices, it may be a service outage — check our
   status page before contacting support.

## Sync Issues (Changes Not Saving or Appearing on Other Devices)

Changes sync automatically within a few seconds when the device has an internet connection.
If sync appears stuck: check the connection indicator in the bottom-left of the app — a yellow
dot means it's retrying, a red dot means it's offline. Signing out and back in forces a full
resync and resolves the vast majority of stuck-sync reports.

## Slow Performance

Performance issues are most often caused by a very large project (several thousand items) on
an older device. Archiving completed items into a separate project usually restores normal
speed. If a single small project is slow, clear the app's local cache from Settings → Advanced
→ Clear Cache (this does not delete any data — it only clears local temp files).

## Integration Errors (Slack, Google Drive, etc.)

If a connected integration stops working, the most common cause is an expired authorization
token. Go to Settings → Integrations, disconnect the affected integration, and reconnect it —
this re-issues a fresh token. If reconnecting fails with an error, check whether the integration
was disabled on the third-party service's side (e.g., a Slack admin revoked app access).

## Mobile App Notifications Not Arriving

Confirm notifications are enabled both in the app (Settings → Notifications) and at the OS
level (iOS/Android system settings for the app). On iOS, notifications silently stop if the
app hasn't been opened in over 30 days — opening the app once restores them.

## When to Escalate a Technical Issue

If a customer has already tried the relevant steps above and the issue persists, or if the
issue looks like a bug affecting multiple customers rather than one account, create a support
ticket for the engineering team rather than repeating the same troubleshooting steps.
