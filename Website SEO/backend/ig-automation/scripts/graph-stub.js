#!/usr/bin/env node
/**
 * A stand-in for graph.instagram.com.
 *
 * Advanced Access is the long pole, and until it lands Meta will not deliver a
 * real `comments` event or accept a private reply. This makes the other 95%
 * testable today: point IG_GRAPH_BASE at it, replay a signed payload, and watch
 * the exact calls the service would have made to Meta.
 *
 * It also enforces the constraint that is easiest to design past and most
 * expensive to get wrong: ONE private reply per comment, ever. A second attempt
 * gets Meta's real error shape back, so the dedupe is proven rather than assumed.
 *
 *   node scripts/graph-stub.js &
 *   IG_GRAPH_BASE=http://127.0.0.1:9099 npm run dev
 */

const express = require("express");

const app = express();
app.use(express.json());

const PORT = process.env.STUB_PORT || 9099;
const repliedTo = new Set();
const calls = [];

const log = (what, extra) => {
  calls.push({ what, ...extra, at: new Date().toISOString() });
  console.log(`  [graph-stub] ${what}`, JSON.stringify(extra));
};

// Every Graph call must carry both. Missing appsecret_proof is a silent
// production failure once the app enforces it, so the stub refuses it here.
app.use((req, res, next) => {
  if (!req.query.access_token) return res.status(400).json({ error: { message: "Missing access token", code: 190 } });
  if (!req.query.appsecret_proof) {
    return res.status(400).json({ error: { message: "appsecret_proof missing", code: 100 } });
  }
  next();
});

app.get("/:version/me", (req, res) => {
  log("whoami");
  res.json({ id: process.env.IG_USER_ID || "17841400000000000", username: "aiprofitlab" });
});

app.post("/:version/:id/messages", (req, res) => {
  const { recipient, message } = req.body || {};

  if (recipient && recipient.comment_id) {
    // Meta's actual behaviour: the private reply is one-shot per comment.
    if (repliedTo.has(recipient.comment_id)) {
      log("private reply REFUSED (already used)", { comment_id: recipient.comment_id });
      return res.status(400).json({
        error: { message: "This comment has already received a private reply.", code: 10, error_subcode: 2534037 },
      });
    }
    repliedTo.add(recipient.comment_id);
    log("private reply", { comment_id: recipient.comment_id, text: message && message.text });
    return res.json({ recipient_id: "78412345678901234", message_id: `mid.${Date.now()}` });
  }

  log("direct message", { to: recipient && recipient.id, text: message && message.text });
  res.json({ recipient_id: recipient && recipient.id, message_id: `mid.${Date.now()}` });
});

app.post("/:version/:commentId/replies", (req, res) => {
  log("public reply", { comment_id: req.params.commentId, message: req.body && req.body.message });
  res.json({ id: `${req.params.commentId}_reply` });
});

// Version-less, matching Meta's documented form:
//   GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&...
// The versioned path is accepted too, so a future API change does not silently
// look like a refresh failure here.
const refresh = (req, res) => {
  if (req.query.grant_type !== "ig_refresh_token") {
    return res.status(400).json({ error: { message: "grant_type must be ig_refresh_token", code: 100 } });
  }
  log("token refresh");
  res.json({ access_token: `IGQ_STUB_${Date.now()}`, token_type: "bearer", expires_in: 5184000 });
};
app.get("/refresh_access_token", refresh);
app.get("/:version/refresh_access_token", refresh);

app.get("/:version/:mediaId", (req, res) => {
  log("media lookup", { media_id: req.params.mediaId });
  res.json({ id: req.params.mediaId, permalink: `https://www.instagram.com/p/STUB${req.params.mediaId.slice(-4)}/`, media_type: "VIDEO" });
});

app.get("/__calls", (req, res) => res.json(calls));
app.use((req, res) => {
  log("UNHANDLED PATH", { method: req.method, path: req.path });
  res.status(404).json({ error: { message: `Unknown Graph path ${req.path}`, code: 803 } });
});

app.listen(PORT, () => console.log(`graph-stub listening on ${PORT} — point IG_GRAPH_BASE at http://127.0.0.1:${PORT}`));
