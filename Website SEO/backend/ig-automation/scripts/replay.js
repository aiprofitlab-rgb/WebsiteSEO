#!/usr/bin/env node
/**
 * Replay a signed webhook payload against a running instance.
 *
 * This is how the whole flow is exercised BEFORE Advanced Access exists — Meta
 * will not deliver a real `comments` event until then, but nothing about this
 * service knows the difference between Meta's POST and this one, because the
 * only thing it checks is the signature.
 *
 *   node scripts/replay.js "storefront"
 *   node scripts/replay.js --email me@example.com
 *   TARGET=https://hooks.aiprofitlab.io/ig node scripts/replay.js "price"
 *
 * Needs META_APP_SECRET set to the same value the server has.
 */

const { sign } = require("../lib/signature");

const TARGET = process.env.TARGET || "http://127.0.0.1:8090/ig";
const SECRET = process.env.META_APP_SECRET || "";
const ACCOUNT = process.env.IG_USER_ID || "17841400000000000";

const args = process.argv.slice(2);
const emailFlag = args.indexOf("--email");
const isEmail = emailFlag !== -1;
const text = isEmail ? args[emailFlag + 1] : args[0] || "storefront";

// A realistic id: exactly 17 digits, which is the length at which USER_ENTERED
// quietly rounds a value on the way into the sheet. Do not shorten it — 16
// digits round-trips fine and the test stops proving anything.
const stamp = Date.now();

// Synthetic ids are fine against scripts/graph-stub.js, which accepts anything.
// They are NOT fine against the real graph.instagram.com: the private reply and
// the public reply both address the comment BY ID, so a made-up one is a 400.
// To drive the real API — which is how the App Review screencast is recorded
// before the comments webhook is switched on — pass the ids of a comment that
// actually exists:
//
//   REPLAY_COMMENT_ID=17... REPLAY_MEDIA_ID=17... REPLAY_IGSID=78... \
//   IG_USER_ID=<your ig id> TARGET=https://hooks.aiprofitlab.io/ig \
//   node scripts/replay.js "price"
//
// scripts/find-comment.js prints all four.
const commentId =
  process.env.REPLAY_COMMENT_ID ||
  ("179" + String(stamp) + String(Math.floor(Math.random() * 1e6)).padStart(6, "0")).slice(0, 17);
const mediaId = process.env.REPLAY_MEDIA_ID || "17900000000000001";
const commenterId = process.env.REPLAY_IGSID || "78412345678901234";

const commentEvent = {
  object: "instagram",
  entry: [
    {
      id: ACCOUNT,
      time: Math.floor(stamp / 1000),
      changes: [
        {
          field: "comments",
          value: {
            id: commentId,
            text,
            from: { id: commenterId, username: "replay_tester" },
            media: { id: mediaId, media_product_type: "REELS" },
          },
        },
      ],
    },
  ],
};

const messageEvent = {
  object: "instagram",
  entry: [
    {
      id: ACCOUNT,
      time: Math.floor(stamp / 1000),
      messaging: [
        {
          sender: { id: commenterId },
          recipient: { id: ACCOUNT },
          timestamp: stamp,
          message: { mid: `m_${stamp}`, text },
        },
      ],
    },
  ],
};

async function main() {
  if (!SECRET) {
    console.error("META_APP_SECRET is not set — the server will reject this as unsigned.");
    process.exit(2);
  }

  const body = Buffer.from(JSON.stringify(isEmail ? messageEvent : commentEvent), "utf8");
  const started = Date.now();

  const res = await fetch(TARGET, {
    method: "POST",
    headers: { "content-type": "application/json", "x-hub-signature-256": sign(body, SECRET) },
    body,
  });

  const ms = Date.now() - started;
  console.log(`${isEmail ? "message" : "comment"} "${text}" -> ${res.status} in ${ms}ms`);
  if (!isEmail) console.log(`comment_id ${commentId}   media ${mediaId}   commenter ${commenterId}`);
  if (!isEmail && !process.env.REPLAY_COMMENT_ID) {
    console.log("(synthetic comment id — against the real Graph API this will fail; set REPLAY_COMMENT_ID)");
  }

  // Meta's budget. Over this and it starts retrying, then disables the callback.
  if (ms > 2000) console.error(`!! ${ms}ms is too slow — Meta expects an ack in about two seconds`);
  if (res.status !== 200) {
    console.error("!! expected 200. 403 means the signature did not match the server's META_APP_SECRET.");
    process.exit(1);
  }
  console.log("Now check the service log for the DM/reply/ledger lines.");
}

main().catch((err) => {
  console.error("REPLAY FAILED:", err && err.message);
  process.exit(1);
});
