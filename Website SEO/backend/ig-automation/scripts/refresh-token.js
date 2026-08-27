#!/usr/bin/env node
/**
 * Daily token rotation. Run from cron or a systemd timer.
 *
 * Instagram long-lived tokens last 60 days and can be refreshed any time after
 * they are 24 hours old, so running this daily means the token is never more
 * than a day from a fresh 60. Missing a run is harmless; missing 60 is fatal.
 *
 * Exits non-zero on a real failure so the timer records it, and emails, because
 * a token that quietly stops refreshing looks exactly like a working system for
 * eight weeks.
 *
 *   node scripts/refresh-token.js
 */

const tokens = require("../lib/tokens");
const alert = require("../lib/mail");

async function main() {
  const before = tokens.daysLeft();
  const result = await tokens.refresh();

  if (result.ok) {
    console.log(JSON.stringify({ token: "refreshed", daysLeft: result.daysLeft, was: before }));
    return 0;
  }

  // Expected on a freshly seeded token. Not an incident.
  if (result.reason === "too-soon") {
    console.log(JSON.stringify({ token: "not-yet-refreshable", daysLeft: before, message: result.message }));
    return 0;
  }

  console.error(JSON.stringify({ token: "REFRESH FAILED", reason: result.reason, message: result.message, daysLeft: before }));
  await alert.tokenRefreshFailed({ reason: result.reason, message: result.message, daysLeft: before }).catch(() => {});
  return 1;
}

main()
  .then((code) => process.exit(code))
  .catch((err) => {
    console.error("REFRESH CRASHED:", err && err.stack);
    process.exit(1);
  });
