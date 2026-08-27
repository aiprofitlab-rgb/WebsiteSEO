/**
 * The webhook endpoint.
 *
 * The GET handshake is lifted from backend/whatsapp-webhook/webhook.js, which
 * already had it right, with two changes: the verify token is compared in
 * constant time, and an unset token is a hard 500 rather than a silent fallback
 * to the string "YOUR_VERIFY_TOKEN" — a placeholder default that anyone can
 * guess is worse than a broken endpoint you notice immediately.
 *
 * The POST handler ACKS FIRST AND WORKS AFTER. Meta gives a webhook a few
 * seconds, retries what it judges failed, and disables a callback that keeps
 * being slow. Sending a DM, posting a reply and appending to a spreadsheet is
 * three network round trips — comfortably over budget. So the only things that
 * happen before the 200 are the signature check and a JSON parse. This is the
 * one structural difference from checkout-api, which is request/response and
 * can afford to answer at the end.
 */

const express = require("express");
const signature = require("./lib/signature");

function create(deps) {
  const router = express.Router();

  // Verification handshake. Meta calls this once, when you save the callback URL.
  router.get("/", (req, res) => {
    const mode = req.query["hub.mode"];
    const token = req.query["hub.verify_token"];
    const challenge = req.query["hub.challenge"];

    const expected = process.env.IG_VERIFY_TOKEN || "";
    if (!expected) {
      console.error("IG_VERIFY_TOKEN is not set — refusing to verify");
      return res.sendStatus(500);
    }
    if (!mode || !token) return res.sendStatus(400);
    if (mode === "subscribe" && signature.safeEqual(token, expected)) {
      console.log("WEBHOOK_VERIFIED");
      return res.status(200).send(challenge);
    }
    console.warn("WEBHOOK VERIFY REJECTED from", req.ip);
    return res.sendStatus(403);
  });

  router.post("/", (req, res) => {
    // Before anything else. This is the only thing standing between a public URL
    // and a stranger forging comment events.
    const ok = signature.verify(req.rawBody, req.get("x-hub-signature-256"), process.env.META_APP_SECRET);
    if (!ok) {
      console.warn("SIGNATURE REJECTED from", req.ip);
      return res.sendStatus(403);
    }

    // Ack now. Everything below is on our own time.
    res.sendStatus(200);

    const body = req.body;
    setImmediate(async () => {
      try {
        const results = await deps.handleEvent(body, deps);
        for (const r of results) {
          if (r.action === "drop") continue; // the common case; not worth a line
          console.log(JSON.stringify({ webhook: r.action, ...r }));
        }
      } catch (err) {
        // Already acked, so this cannot become a response. It must never become
        // an unhandled rejection either, or the process exits.
        console.error("WEBHOOK PROCESSING FAILED:", err && err.stack);
      }
    });
  });

  return router;
}

module.exports = { create };
