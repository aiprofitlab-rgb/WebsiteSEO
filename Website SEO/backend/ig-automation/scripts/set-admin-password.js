#!/usr/bin/env node
/**
 * Turn a password into the line that goes in /etc/ig-automation/.env.
 *
 *   node scripts/set-admin-password.js
 *
 * The hash is what the service stores; the password itself is never written
 * anywhere, and never echoed. Changing it also signs out every open session,
 * because the cookie signing key is derived from the hash.
 *
 * A password can be passed as argv[2] for a scripted install, but not from an
 * interactive shell — it would land in the history file, which is the one place
 * a password on this box must not be.
 */

const readline = require("node:readline");
const crypto = require("node:crypto");

const auth = require("../lib/auth");

/** readline with the echo suppressed, so nothing reaches the scrollback. */
function askHidden(prompt) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
    let asked = false;
    rl._writeToOutput = (chunk) => {
      // The prompt itself prints once; the typed characters never do.
      if (!asked) {
        asked = true;
        rl.output.write(prompt);
      }
    };
    rl.question(prompt, (answer) => {
      rl.close();
      process.stdout.write("\n");
      resolve(answer);
    });
  });
}

(async () => {
  let password = process.argv[2];
  if (!password) {
    password = await askHidden("New admin password: ");
    const again = await askHidden("Again: ");
    if (password !== again) {
      console.error("They do not match.");
      process.exit(1);
    }
  }

  if (String(password).length < 12) {
    console.error(`\nThat is ${String(password).length} characters. This panel can rewrite what the account says to`);
    console.error("every follower who comments, and it sits on a public hostname. Use at least 12.\n");
    console.error(`A good one: ${crypto.randomBytes(12).toString("base64url")}`);
    process.exit(1);
  }

  console.log("\nPut this in /etc/ig-automation/.env, then: sudo systemctl restart ig-automation\n");
  console.log(`IG_ADMIN_PASSWORD_HASH='${auth.hash(password)}'\n`);
  console.log("Every open session is signed out by this change. The password itself is stored nowhere.");
})();
