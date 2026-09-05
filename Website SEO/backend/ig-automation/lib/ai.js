/**
 * The fallback brain: what to say when no keyword matched.
 *
 * Plain fetch against the OpenAI chat API rather than the `openai` SDK, for the
 * same reason lib/ig.js hand-rolls Graph: one more native-free dependency on the
 * VPS buys nothing here. Shape follows lib/ig.js — a create() that closes over
 * config, an error type carrying the upstream code, and a hard timeout, because
 * this runs after the webhook has already been acked and a hung socket would
 * pin a handler open indefinitely.
 *
 * TWO RULES GOVERN EVERYTHING BELOW.
 *
 * 1. SILENCE IS ALWAYS SAFE. Every failure path returns null, and null means the
 *    service says nothing at all. A missing key, a 429, a timeout, a refusal, a
 *    reply that trips a guard — all of them end the same way. Not answering a
 *    comment costs a lead; answering a hundred times, or answering wrongly in
 *    public under the brand's own post, costs the account.
 *
 * 2. THE OUTPUT MUST NOT BE ABLE TO TRIGGER US. A generated public reply is a
 *    new comment on our own post the moment it lands. If it happens to contain
 *    the word "demo", the demo rule fires on it, and the account is back in the
 *    2026-08-30 loop with better prose. So the live keywords are named in the
 *    prompt as forbidden AND the finished text is re-checked against the very
 *    matcher the webhook will run on it. The check is the guarantee; the prompt
 *    only makes the check rarely fire.
 */

const rulesLib = require("./rules");

const ENDPOINT = process.env.IG_AI_ENDPOINT || "https://api.openai.com/v1/chat/completions";
const TIMEOUT_MS = Number(process.env.IG_AI_TIMEOUT_MS || 12_000);

/** The model's way of declining. Anything containing it means "say nothing". */
const SKIP = "SKIP";

class AiError extends Error {
  constructor(message, meta = {}) {
    super(message);
    this.name = "AiError";
    Object.assign(this, meta);
  }
}

/**
 * Which language to answer in, decided here rather than by the model.
 *
 * Asking a model to "match the language of the message" reads as sufficient and
 * is not. The forbidden-words list below carries every Arabic keyword the rules
 * listen for — متجر, سعر, دليل, تجربة — so by the time the system prompt is
 * assembled it is visibly bilingual, and a short English comment loses the
 * argument: the first live test answered "do you work with businesses outside
 * oman?" entirely in Arabic. The script of the incoming text is a fact we
 * already have, so it is stated as an instruction instead of left to inference.
 *
 * Arabic if any Arabic letter appears at all, not if most do: a message is
 * routinely "أوكي thanks" and the person's own language is the one they opened
 * in. Everything else — including Persian and Urdu, which share the block —
 * gets the same treatment, which is correct: reply in the script they used.
 */
const ARABIC_SCRIPT = /[\u0600-\u06FF\u0750-\u077F]/;

function languageInstruction(text) {
  return ARABIC_SCRIPT.test(String(text || ""))
    ? "- The person wrote in ARABIC. Your entire reply must be in Arabic."
    : "- The person wrote in ENGLISH. Your entire reply must be in English, even though some trigger words listed above are Arabic — that list is not a hint about which language to use.";
}

/** Every keyword the rules are currently listening for, flattened for the prompt. */
function liveKeywords(rulesConfig) {
  const out = new Set();
  for (const rule of (rulesConfig && rulesConfig.rules) || []) {
    if (rule.enabled === false) continue;
    for (const k of rule.keywords || []) if (k) out.add(String(k));
  }
  return [...out];
}

/**
 * The system prompt. Assembled rather than stored whole so that the parts a
 * person edits (persona, facts, rules) stay separate from the parts the service
 * must control (the length cap, the forbidden words, the SKIP contract).
 */
function systemPrompt(cfg, { surface, maxChars, forbidden, language }) {
  const lines = [];
  if (cfg.persona) lines.push(cfg.persona);

  if (cfg.facts && cfg.facts.length) {
    lines.push("", "What you know:");
    for (const f of cfg.facts) lines.push(`- ${f}`);
  }

  if (cfg.rules && cfg.rules.length) {
    lines.push("", "How to answer:");
    for (const r of cfg.rules) lines.push(`- ${r}`);
  }

  lines.push("", "Hard limits:");
  lines.push(
    surface === "comment"
      ? `- This is a PUBLIC reply under an Instagram comment. Everyone can read it. One or two sentences, ${maxChars} characters at the absolute most.`
      : `- This is a private Instagram DM. Keep it under ${maxChars} characters, and write it as one short paragraph, not a list.`
  );

  // The reason this line exists is in the header. It is belt; the post-check is braces.
  if (forbidden.length) {
    lines.push(
      `- NEVER use any of these words, in any language, even in passing: ${forbidden.join(", ")}. ` +
        "They are trigger words on this account and using one would make the account reply to itself."
    );
  }

  // Last, deliberately. The instruction the model is most likely to drop is the
  // one furthest from the end of the prompt, and this is the one a follower
  // notices immediately when it goes wrong.
  if (language) lines.push(language);

  lines.push(`- Reply with the message text only. No quotes around it, no "Reply:", no preamble.`);
  lines.push(`- If you should not answer at all, reply with exactly ${SKIP} and nothing else.`);

  return lines.join("\n");
}

function create({ apiKey = process.env.OPENAI_API_KEY, fetchImpl = fetch } = {}) {
  const key = () => (typeof apiKey === "function" ? apiKey() : apiKey) || "";

  async function complete(messages, cfg) {
    if (!key()) throw new AiError("No OPENAI_API_KEY configured", { code: "NO_KEY" });

    let res, payload;
    try {
      res = await fetchImpl(ENDPOINT, {
        method: "POST",
        headers: { "content-type": "application/json", authorization: `Bearer ${key()}` },
        body: JSON.stringify({
          model: cfg.model,
          messages,
          temperature: cfg.temperature,
          // Sized to the surface, not generous. A model given room to ramble on
          // a public Instagram comment will use it.
          max_tokens: cfg.surface === "comment" ? 160 : 400,
        }),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
      payload = await res.json().catch(() => ({}));
    } catch (err) {
      throw new AiError(`completion failed: ${err && err.message}`, { code: "NETWORK" });
    }

    if (!res.ok || payload.error) {
      const e = payload.error || {};
      throw new AiError(e.message || `HTTP ${res.status}`, { status: res.status, code: e.code || e.type });
    }

    const text = payload.choices && payload.choices[0] && payload.choices[0].message && payload.choices[0].message.content;
    return String(text || "").trim();
  }

  /**
   * Clean up and vet what came back.
   *
   * @returns {string|null} the text to send, or null to stay silent.
   */
  function vet(raw, { surface, maxChars, rulesConfig, mediaId }) {
    let text = String(raw || "").trim();
    if (!text) return null;

    // Models like to wrap a one-line answer in quotes despite being told not to.
    text = text.replace(/^["'“”](.*)["'“”]$/s, "$1").trim();

    // The decline contract. Checked on the whole reply, not a prefix: a model
    // that says "SKIP — this needs a human" still means skip.
    if (!text || text.toUpperCase().includes(SKIP)) return null;

    // A public comment reply is one block of text. Line breaks in an Instagram
    // comment read as a stray bullet list and, worse, invite the model to send
    // a multi-part answer where one sentence was asked for.
    if (surface === "comment") text = text.replace(/\s*\n+\s*/g, " ").trim();

    if (text.length > maxChars) {
      /**
       * Prefer to end on a complete sentence, even at the cost of a good deal of
       * the budget. A public comment that stops mid-word behind an ellipsis
       * looks broken in a way a short one does not — and the reader cannot tap
       * "more", because there is no more. The 40% floor only stops the pathology
       * where an opening "Hi!" is the sole survivor of a long answer.
       *
       * The ellipsis is counted, not appended after the fact. Adding it to a cut
       * already exactly maxChars long is how a cap quietly becomes maxChars + 1.
       */
      const cut = text.slice(0, maxChars);
      const stop = Math.max(cut.lastIndexOf(". "), cut.lastIndexOf("! "), cut.lastIndexOf("? "));
      text = (stop > maxChars * 0.4 ? cut.slice(0, stop + 1) : text.slice(0, maxChars - 1).trimEnd() + "…").trim();
    }

    // THE GUARANTEE. Run the finished text through the same matcher the webhook
    // will run on it when Meta hands it back as a new comment. If it would fire
    // a rule, it is a loop waiting to happen, and there is no version of sending
    // it that is safe. Only matters for the public surface — a DM never comes
    // back as a comment — but checking both costs nothing and a future surface
    // that forgets this is exactly how the guard gets lost.
    const collision = rulesLib.match(text, rulesConfig, { mediaId: mediaId || "" });
    if (collision) {
      console.error(
        `AI REPLY SUPPRESSED: it contains the keyword "${collision.keyword}" (rule ${collision.rule.id}) and would make the account answer itself`
      );
      return null;
    }

    return text || null;
  }

  /** One user message plus whatever history there is, in the model's own format. */
  const asTurns = (history) =>
    (history || [])
      .filter((t) => t && t.text)
      .map((t) => ({ role: t.role === "assistant" ? "assistant" : "user", content: String(t.text) }));

  return {
    AiError,
    configured: () => Boolean(key()),

    /**
     * A public answer to a comment that matched no keyword.
     * @returns {Promise<string|null>}
     */
    async replyToComment({ text, username, config, rulesConfig, mediaId }) {
      const maxChars = Number(config.comments.maxChars) || 280;
      const forbidden = liveKeywords(rulesConfig);
      const sys = systemPrompt(config, { surface: "comment", maxChars, forbidden, language: languageInstruction(text) });

      const raw = await complete(
        [
          { role: "system", content: sys },
          {
            role: "user",
            content: `${username ? `@${username}` : "Someone"} commented on one of our posts:\n\n${text}`,
          },
        ],
        { model: config.model, temperature: config.temperature, surface: "comment" }
      );

      return vet(raw, { surface: "comment", maxChars, rulesConfig, mediaId });
    },

    /**
     * A DM answer. `history` is oldest-first, from store.transcript().
     * @returns {Promise<string|null>}
     */
    async replyToDm({ text, username, history, config, rulesConfig }) {
      const maxChars = Number(config.dms.maxChars) || 700;
      const forbidden = liveKeywords(rulesConfig);
      const sys = systemPrompt(config, { surface: "dm", maxChars, forbidden, language: languageInstruction(text) });

      const raw = await complete(
        [
          { role: "system", content: sys },
          ...(username ? [{ role: "system", content: `You are talking to @${username}.` }] : []),
          ...asTurns(history),
          { role: "user", content: String(text) },
        ],
        { model: config.model, temperature: config.temperature, surface: "dm" }
      );

      // No mediaId: a DM is not under a post, so an unscoped rule is the only
      // thing that could collide, which is what passing an empty id asks about.
      return vet(raw, { surface: "dm", maxChars, rulesConfig });
    },
  };
}

module.exports = { create, AiError, liveKeywords, systemPrompt, languageInstruction, SKIP };
