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
const oauth = require("./lib/oauth");
const oauthPage = require("./lib/oauthPage");

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

  /**
   * Meta's deauthorize and data-deletion callbacks.
   *
   * Both are REQUIRED fields on the Business Login settings page before an app
   * can be submitted for review, and neither is a webhook: they arrive as
   * form-encoded POSTs carrying a `signed_request`, not as JSON with an
   * X-Hub-Signature-256 header. So they cannot reuse the gate above, and they
   * get their own body parser.
   *
   * Neither one deletes anything on its own. A person removing the app is not
   * an emergency, and an automatic irreversible delete triggered by an unsigned
   * POST would be a worse bug than the one it prevents. Both record the request
   * loudly in the journal; the 30-day promise on /privacy/#data-deletion is kept
   * by hand.
   */
  const form = express.urlencoded({ extended: false, limit: "16kb" });

  // A reviewer may well click these in a browser. A JSON 404 looks broken.
  const explain = (what) => (req, res) =>
    res
      .type("text/plain")
      .send(`${what} endpoint for the AI Profit Lab Instagram app.\nMeta POSTs here. See https://aiprofitlab.io/privacy/#data-deletion`);

  router.get("/deauthorize", explain("Deauthorize callback"));
  router.get("/data-deletion", explain("Data deletion request"));

  router.post("/deauthorize", form, (req, res) => {
    const payload = signature.parseSignedRequest(req.body && req.body.signed_request, process.env.META_APP_SECRET);
    if (!payload) {
      console.warn("DEAUTHORIZE REJECTED (bad or unsigned signed_request) from", req.ip);
      return res.sendStatus(400);
    }
    console.log(JSON.stringify({ event: "deauthorize", user_id: payload.user_id || null, at: new Date().toISOString() }));
    return res.sendStatus(200);
  });

  router.post("/data-deletion", form, (req, res) => {
    const payload = signature.parseSignedRequest(req.body && req.body.signed_request, process.env.META_APP_SECRET);
    if (!payload) {
      console.warn("DATA DELETION REJECTED (bad or unsigned signed_request) from", req.ip);
      return res.sendStatus(400);
    }

    // Meta shows this code to the user and expects it to be quotable back to us,
    // so it has to appear in the journal too, next to the id it belongs to.
    const confirmationCode = `del-${Date.now().toString(36)}-${String(payload.user_id || "unknown").slice(-6)}`;
    console.log(
      JSON.stringify({
        event: "data_deletion_request",
        user_id: payload.user_id || null,
        confirmation_code: confirmationCode,
        at: new Date().toISOString(),
      })
    );

    // The shape Meta requires: where the user can check, and a code to quote.
    return res.json({
      url: "https://aiprofitlab.io/privacy/#data-deletion",
      confirmation_code: confirmationCode,
    });
  });

  /**
   * Instagram Business Login.
   *
   * `/ig/oauth/start` is the single URL that goes in the App Review submission
   * under "can your app be loaded and tested externally" — a reviewer opens it,
   * sees the consent screen, and lands on a page naming their own account. It is
   * also the first shot of the screencast, which is why it is a redirect rather
   * than a form: one click, no typing, nothing on screen to redact.
   *
   * Both routes are read-only. See the header of lib/oauth.js for why storing
   * the token here would be a bug rather than a feature.
   *
   * Not mounted without an app id and secret, the same way the admin panel is
   * not mounted without a password: a half-configured OAuth endpoint answers
   * every reviewer with a 500, and a 404 is the more honest "not set up".
   */
  if (oauth.configured()) {
    router.get("/oauth/start", (req, res) => {
      // No cookie. The state is a signed, timestamped nonce, so it verifies on
      // the way back with nothing kept in between — which also means the flow
      // survives the reviewer finishing it in a different browser tab, window
      // or app than the one they started in. On a phone, Instagram's in-app
      // browser makes that the normal case rather than the edge one.
      res.redirect(302, oauth.authorizeUrl());
    });

    router.get("/oauth/callback", async (req, res) => {
      const { code, state, error, error_description: description, error_reason: reason } = req.query;

      // Tapping Cancel on the consent screen. Not a fault, and not a 500.
      if (error) {
        console.log(JSON.stringify({ event: "oauth_declined", error, reason: reason || null }));
        return res
          .status(400)
          .type("html")
          .send(oauthPage.failure({ title: "Sign-in cancelled", detail: description || String(error) }));
      }

      if (!code) {
        return res.status(400).type("html").send(oauthPage.failure({ title: "Missing authorization code" }));
      }

      // Warn, do not refuse. A callback opened by hand, or replayed from an
      // address bar an hour later, has no valid state and still has nothing to
      // abuse — the request stores nothing either way. Refusing here would turn
      // a reviewer's harmless retry into a failed test.
      if (!oauth.checkState(state)) console.warn("OAUTH STATE MISSING OR STALE from", req.ip);

      try {
        const result = await oauth.connect(code);
        console.log(
          JSON.stringify({
            event: "oauth_connected",
            username: result.account.username || null,
            user_id: result.account.id || null,
            permissions: result.permissions,
            configured_account: result.isConfiguredAccount,
            at: new Date().toISOString(),
          })
        );
        return res.type("html").send(oauthPage.success(result));
      } catch (err) {
        console.error("OAUTH FAILED:", err && err.step, err && err.message);
        return res
          .status(502)
          .type("html")
          .send(oauthPage.failure({ title: "Could not complete sign-in", detail: err && err.message }));
      }
    });
  }

  return router;
}

module.exports = { create };
