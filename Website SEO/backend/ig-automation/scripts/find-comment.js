#!/usr/bin/env node
/**
 * Print the ids the App Review screencast needs.
 *
 * Before Advanced Access, Meta does not deliver a `comments` event, so the flow
 * has to be started by hand — but the private reply and the public reply both
 * address the comment BY ID, so the id has to be a real one. This asks Instagram
 * for it.
 *
 *   IG_ACCESS_TOKEN=IGAA... node scripts/find-comment.js
 *   IG_ACCESS_TOKEN=IGAA... node scripts/find-comment.js <MEDIA_ID>
 *
 * With no argument it lists recent posts. With a media id it lists that post's
 * comments, newest first, and prints the ready-made replay command.
 *
 * Read-only. It sends nothing to anybody.
 */

const { appsecretProof } = require("../lib/signature");

const BASE = process.env.IG_GRAPH_BASE || "https://graph.instagram.com";
const VERSION = process.env.IG_API_VERSION || "v20.0";
const TOKEN = process.env.IG_ACCESS_TOKEN || "";
const SECRET = process.env.META_APP_SECRET || "";

async function get(path, fields) {
  const url = new URL(`${BASE}/${VERSION}/${path}`);
  if (fields) url.searchParams.set("fields", fields);
  url.searchParams.set("access_token", TOKEN);
  if (SECRET) url.searchParams.set("appsecret_proof", appsecretProof(TOKEN, SECRET));

  const res = await fetch(url);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = (body && body.error) || {};
    throw new Error(`${res.status} ${err.code || ""} ${err.message || JSON.stringify(body)}`);
  }
  return body;
}

async function main() {
  if (!TOKEN) {
    console.error("IG_ACCESS_TOKEN is not set. Paste the IGAA... token from the App Dashboard.");
    process.exit(2);
  }

  const me = await get("me", "id,username");
  console.log(`account   @${me.username}  IG_USER_ID=${me.id}\n`);

  const mediaId = process.argv[2];

  if (!mediaId) {
    const { data = [] } = await get("me/media", "id,caption,permalink,timestamp");
    console.log("recent posts — pick one and run this again with its id:\n");
    for (const m of data.slice(0, 10)) {
      const caption = String(m.caption || "").replace(/\s+/g, " ").slice(0, 60);
      console.log(`  ${m.id}  ${String(m.timestamp || "").slice(0, 10)}  ${caption}`);
      console.log(`  ${" ".repeat(m.id.length)}  ${m.permalink}\n`);
    }
    return;
  }

  const { data = [] } = await get(`${mediaId}/comments`, "id,text,username,from,timestamp");
  if (!data.length) {
    console.log("no comments on that post yet.");
    return;
  }

  const newest = [...data].sort((a, b) => String(b.timestamp).localeCompare(String(a.timestamp)));
  console.log("comments, newest first:\n");
  for (const c of newest) {
    const who = c.username || (c.from && c.from.username) || "?";
    console.log(`  ${c.id}  @${who}: ${String(c.text || "").replace(/\s+/g, " ").slice(0, 60)}`);
  }

  const c = newest[0];
  const igsid = (c.from && c.from.id) || "";
  console.log(`\nto drive the flow for the newest comment (@${c.username || (c.from && c.from.username) || "?"}):\n`);
  console.log(
    [
      `  REPLAY_COMMENT_ID=${c.id} \\`,
      `  REPLAY_MEDIA_ID=${mediaId} \\`,
      igsid ? `  REPLAY_IGSID=${igsid} \\` : `  REPLAY_IGSID=<not returned — leave the default> \\`,
      `  IG_USER_ID=${me.id} \\`,
      `  META_APP_SECRET=<same secret the server has> \\`,
      `  TARGET=https://hooks.aiprofitlab.io/ig \\`,
      `  node scripts/replay.js ${JSON.stringify(String(c.text || "").trim())}`,
    ].join("\n")
  );
}

main().catch((err) => {
  console.error("FAILED:", err && err.message);
  process.exit(1);
});
