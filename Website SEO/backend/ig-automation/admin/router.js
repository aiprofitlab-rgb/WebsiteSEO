/**
 * The admin panel's API.
 *
 * Everything the panel can do is here, and everything here is one of five
 * things: sign in, read the current state, save rules, manage files, or look at
 * what the automation has actually been doing. There is no endpoint that sends
 * a DM or posts a comment — the panel configures the automation, it does not
 * drive Instagram by hand. That line is deliberate: a "send test DM" button
 * would burn the one private reply a comment ever gets.
 *
 * Two rules hold everywhere below:
 *
 *   Nothing writes without passing rulesLib.inspect(). The panel is the fastest
 *   way to configure a reply loop and it is the one place that must refuse to.
 *
 *   Nothing leaks a secret into the browser. The state payload reports whether
 *   the app secret and token exist, never what they are.
 */

const express = require("express");

const auth = require("../lib/auth");
const files = require("../lib/files");
const rulesLib = require("../lib/rules");
const rulesStore = require("../lib/rulesStore");

const UPLOAD_LIMIT = `${Math.round(files.MAX_BYTES / 1024 / 1024) + 1}mb`;

/** Media list from Graph, cached — the panel re-renders far more often than the account posts. */
const mediaCache = { at: 0, items: [], error: null };
const MEDIA_TTL_MS = 5 * 60_000;

function create(deps) {
  const router = express.Router();
  const secureCookies = process.env.IG_ADMIN_INSECURE_COOKIES !== "1";

  /* ---------------- session ---------------- */

  router.post("/api/login", express.json({ limit: "4kb" }), auth.sameOrigin, (req, res) => {
    const wait = auth.lockedFor(req.ip);
    if (wait > 0) {
      return res.status(429).json({ message: `Too many attempts. Try again in ${Math.ceil(wait / 60000)} minutes.` });
    }
    const ok = auth.verifyPassword((req.body && req.body.password) || "", auth.storedHash());
    if (!ok) {
      auth.recordFailure(req.ip);
      console.warn("ADMIN LOGIN FAILED from", req.ip);
      return res.status(401).json({ message: "Wrong password." });
    }
    auth.clearFailures(req.ip);
    auth.setCookie(res, auth.issue(), { secure: secureCookies });
    console.log(JSON.stringify({ event: "admin_login", ip: req.ip, at: new Date().toISOString() }));
    res.json({ ok: true, expiresInHours: Math.round(auth.ttlMs() / 3600000) });
  });

  router.post("/api/logout", (req, res) => {
    auth.clearCookie(res, { secure: secureCookies });
    res.json({ ok: true });
  });

  /**
   * Pre-auth, so it carries only what the login card needs to name itself:
   * the handle the service actually resolved at boot. Public already —
   * /health reports it, and an Instagram username is not a secret — but it
   * keeps the sign-in page from claiming an account we do not drive.
   */
  router.get("/api/session", (req, res) => {
    res.json({
      authed: Boolean(auth.readToken(auth.fromRequest(req))),
      configured: auth.configured(),
      username: deps.selfUsername || null,
    });
  });

  // Everything past this point needs a session.
  router.use("/api", auth.requireAuth);

  /* ---------------- state ---------------- */

  /**
   * One request, everything the panel draws with. Deliberately not five
   * endpoints the page has to sequence: the rules and the file list have to
   * agree with each other, and the etag returned here is what the next save is
   * checked against.
   */
  router.get("/api/state", (req, res) => {
    const config = rulesStore.current();
    const list = files.list();
    res.json({
      rules: config,
      etag: rulesStore.etag(),
      problems: rulesLib.inspect(config),
      files: list,
      limits: {
        maxUploadMB: Math.round(files.MAX_BYTES / 1024 / 1024),
        allowedTypes: Object.keys(files.TYPES),
        perMediaPerHour: deps.limits && deps.limits.perMediaPerHour,
        perAccountPerHour: deps.limits && deps.limits.perAccountPerHour,
      },
      account: {
        id: deps.selfId || null,
        username: deps.selfUsername || null,
        tokenDaysLeft: deps.tokens ? deps.tokens.daysLeft() : null,
        appSecret: Boolean(process.env.META_APP_SECRET),
        verifyToken: Boolean(process.env.IG_VERIFY_TOKEN),
        ledger: deps.ledger && deps.ledger.enabled && deps.ledger.enabled() ? "sheet" : "logs",
        publicBase: files.publicBase(),
      },
      rulesFile: rulesStore.file(),
      backups: rulesStore.backups().slice(0, 10),
    });
  });

  /* ---------------- rules ---------------- */

  router.put("/api/rules", express.json({ limit: "512kb" }), auth.sameOrigin, (req, res) => {
    try {
      const result = rulesStore.save(req.body && req.body.rules ? req.body : { rules: [] }, {
        ifMatch: (req.body && req.body.etag) || undefined,
        actor: "panel",
      });
      res.json({ ok: true, rules: result.config, etag: result.etag, problems: result.problems });
    } catch (err) {
      if (err instanceof rulesStore.RulesRejected) {
        return res.status(422).json({ message: "These rules were not saved.", problems: err.problems });
      }
      if (err instanceof rulesStore.RulesConflict) {
        return res.status(409).json({
          message: "Someone saved a change in another tab. Reload before saving, or your edit would overwrite theirs.",
          etag: err.actual,
        });
      }
      console.error("RULES SAVE FAILED:", err && err.stack);
      res.status(500).json({ message: "Could not write the rules file." });
    }
  });

  /**
   * Dry run. "If someone commented THIS on THAT post, what happens?"
   *
   * The single most useful thing in the panel, because keyword order, post
   * targeting and Arabic normalisation all interact and none of them are
   * visible by reading the form. It touches nothing.
   */
  router.post("/api/rules/preview", express.json({ limit: "64kb" }), (req, res) => {
    const body = req.body || {};
    // Preview the UNSAVED draft when the panel sends one, so the button answers
    // for what is on screen rather than what is on disk.
    const config = body.rules ? rulesStore.normaliseConfig(body) : rulesStore.current();
    const text = String(body.text || "");
    const mediaId = body.mediaId == null ? undefined : String(body.mediaId);

    if (rulesLib.isOwnReplyText(text, config)) {
      return res.json({ outcome: "dropped", why: "this is one of your own public replies — the loop guard drops it" });
    }
    const hit = mediaId === undefined ? rulesLib.match(text, config) : rulesLib.match(text, config, { mediaId });
    if (!hit) return res.json({ outcome: "dropped", why: "no rule matches this comment on this post" });

    const fileUrl = hit.rule.dm && hit.rule.dm.fileId ? files.urlFor(hit.rule.dm.fileId) : "";
    res.json({
      outcome: "sent",
      ruleId: hit.rule.id,
      ruleName: hit.rule.name || hit.rule.id,
      keyword: hit.keyword,
      dm: rulesLib.dmText(hit.rule, { fileUrl }),
      publicReply: hit.rule.publicReply || "",
      askEmail: Boolean(hit.rule.askEmail),
    });
  });

  router.post("/api/rules/restore", express.json({ limit: "4kb" }), auth.sameOrigin, (req, res) => {
    const config = rulesStore.readBackup(req.body && req.body.name);
    if (!config) return res.status(404).json({ message: "No such backup." });
    try {
      const result = rulesStore.save(config, { actor: "panel/restore" });
      res.json({ ok: true, rules: result.config, etag: result.etag, problems: result.problems });
    } catch (err) {
      if (err instanceof rulesStore.RulesRejected) {
        return res.status(422).json({ message: "That backup no longer validates.", problems: err.problems });
      }
      throw err;
    }
  });

  /* ---------------- posts ---------------- */

  /**
   * The account's posts and reels, for the picker.
   *
   * Cached for five minutes and served stale on a Graph failure: a token blip
   * should leave the panel usable — the ids in the rules are what matter, and
   * they do not change — rather than emptying the picker and inviting someone
   * to "fix" a rule by clearing its targeting.
   */
  router.get("/api/media", async (req, res) => {
    const fresh = req.query.refresh === "1";
    const now = Date.now();
    if (!fresh && mediaCache.items.length && now - mediaCache.at < MEDIA_TTL_MS) {
      return res.json({ items: mediaCache.items, cachedAt: new Date(mediaCache.at).toISOString(), stale: false });
    }
    try {
      const payload = await deps.ig.mediaList({ limit: Number(req.query.limit) || 50 });
      mediaCache.items = (payload.data || []).map((m) => ({
        id: String(m.id),
        caption: String(m.caption || "").slice(0, 220),
        type: m.media_type || "",
        thumb: m.thumbnail_url || m.media_url || "",
        permalink: m.permalink || "",
        timestamp: m.timestamp || "",
      }));
      mediaCache.at = now;
      mediaCache.error = null;
      res.json({ items: mediaCache.items, cachedAt: new Date(now).toISOString(), stale: false });
    } catch (err) {
      mediaCache.error = err && err.message;
      console.error("MEDIA LIST FAILED:", err && err.message);
      res.json({
        items: mediaCache.items,
        cachedAt: mediaCache.at ? new Date(mediaCache.at).toISOString() : null,
        stale: true,
        error: `Could not reach Instagram: ${err && err.message}`,
      });
    }
  });

  /* ---------------- files ---------------- */

  /**
   * Upload.
   *
   * Raw body, filename in a header, rather than multipart/form-data — which
   * would mean a parser dependency for a form with one field. The browser sends
   * the File object straight through with fetch(); nothing is lost and the
   * service keeps its three dependencies.
   */
  router.post("/api/files", express.raw({ type: "*/*", limit: UPLOAD_LIMIT }), auth.sameOrigin, (req, res) => {
    try {
      const saved = files.save(req.body, req.get("x-filename") || "upload");
      res.status(201).json({ ok: true, file: saved });
    } catch (err) {
      if (err instanceof files.UploadRejected) return res.status(400).json({ message: err.message });
      console.error("UPLOAD FAILED:", err && err.stack);
      res.status(500).json({ message: "Could not store the file." });
    }
  });

  router.delete("/api/files/:id", auth.sameOrigin, (req, res) => {
    const inUse = files.usedBy(req.params.id, rulesStore.current());
    // A rule pointing at a deleted file sends its text and link and quietly
    // drops the attachment, which is a bad thing to discover from a follower.
    if (inUse.length && req.query.force !== "1") {
      return res.status(409).json({ message: `Still attached to: ${inUse.join(", ")}. Detach it first.`, inUse });
    }
    res.json({ ok: files.remove(req.params.id) });
  });

  /* ---------------- what actually happened ---------------- */

  /**
   * The last N comments the service took on. This is the answer to "is my new
   * rule working", which is otherwise a journalctl session over SSH.
   */
  router.get("/api/activity", (req, res) => {
    const limit = Math.min(Number(req.query.limit) || 40, 200);
    const rows = deps.store.recent ? deps.store.recent(limit) : [];
    res.json({
      items: rows.map((r) => ({
        commentId: r.comment_id,
        mediaId: r.media_id,
        username: r.username,
        ruleId: r.rule_id,
        status: r.status,
        notes: r.notes,
        at: new Date(r.claimed_at).toISOString(),
      })),
      stats: deps.store.stats(),
    });
  });

  return router;
}

module.exports = { create };
