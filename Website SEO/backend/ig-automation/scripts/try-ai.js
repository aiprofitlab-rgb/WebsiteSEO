#!/usr/bin/env node
/**
 * Hear what the fallback would say, without spending a public reply to find out.
 *
 * Tone is the one thing in this service that cannot be unit-tested and cannot be
 * tried in production either: a comment reply is public, permanent-ish, and the
 * account has one shot at being funny in front of the people who already follow
 * it. So this runs the REAL config, the REAL prompt and the REAL guards against
 * a line you type, and prints the result instead of posting it.
 *
 *   node --env-file=.env scripts/try-ai.js "do you build websites?"
 *   node --env-file=.env scripts/try-ai.js --dm "who runs this account?"
 *   node --env-file=.env scripts/try-ai.js --prompt "هل تعملون خارج عمان؟"
 *   node --env-file=.env scripts/try-ai.js --media=17900000000000000 "nice work"
 *
 * On the VPS the key and the live config are already in the environment:
 *
 *   sudo -u igbot IG_AI_FILE=/var/lib/ig-automation/ai.json \
 *     IG_RULES_FILE=/var/lib/ig-automation/rules.json \
 *     node scripts/try-ai.js "your test comment"
 *
 * WHAT "no reply" MEANS HERE. Three different outcomes look like silence on
 * Instagram and this tells them apart: the model chose SKIP, the reply tripped
 * the keyword guard (lib/ai.js prints AI REPLY SUPPRESSED just above), or the
 * call failed. Only the third is a fault.
 *
 * The caps, the dedupe table and the loop breaker are NOT consulted — they are
 * handler.js's job and they are about how often, not about what. Nothing is
 * posted and nothing is written to the database.
 *
 * The site index IS fetched, once, before anything else — the live one, over the
 * network, which is the only place this service ever does that outside its timer.
 * Without it --prompt would show a prompt with no reference block and quietly
 * misrepresent what the model is actually being handed.
 */

const aiConfig = require("../lib/aiConfig");
const rulesStore = require("../lib/rulesStore");
const aiLib = require("../lib/ai");
const siteIndex = require("../lib/siteIndex");

const argv = process.argv.slice(2);
const flag = (name) => argv.some((a) => a === `--${name}`);
const value = (name) => {
  const hit = argv.find((a) => a.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : "";
};

const text = argv.filter((a) => !a.startsWith("--")).join(" ").trim();
const surface = flag("dm") ? "dm" : "comment";
const mediaId = value("media");
const username = value("as") || "someone";

async function main() {
  if (!text) {
    console.error('Nothing to answer. Try: node scripts/try-ai.js "do you build websites?"');
    process.exit(2);
  }

  const config = aiConfig.current();
  const rulesConfig = rulesStore.current();
  const ai = aiLib.create({ apiKey: () => process.env.OPENAI_API_KEY });

  // Worth saying rather than silently answering from the seed: the whole point
  // of the exercise is to preview the config that will actually run.
  console.log(`config:   ${aiConfig.file()}${config.enabled ? "" : "   ** enabled:false — live, this would say nothing **"}`);
  console.log(`rules:    ${rulesStore.file()}`);
  console.log(`model:    ${config.model} @ temperature ${config.temperature}`);
  console.log(`surface:  ${surface}${mediaId ? ` on media ${mediaId}` : " (no media id — only unscoped rules can suppress the reply)"}`);

  // Plan B. Failures print their own line inside refresh() and are not fatal
  // here for the same reason they are not fatal live: the answer is built from
  // `facts` either way.
  const ic = config.index || {};
  if (!ic.enabled) {
    console.log("index:    off (`index.enabled` is false) — answering from `facts` alone");
  } else {
    const loaded = await siteIndex.refresh(config);
    const st = siteIndex.stats();
    console.log(
      loaded && loaded.ok
        ? `index:    ${st.pages} pages of ${st.seen} from ${ic.url}, generated ${st.generated} (${st.dropped.figure} dropped for a figure, ${st.dropped.money} for being about money)`
        : `index:    NOT LOADED — the block below will be missing, everything else is unaffected`
    );
  }

  if (flag("prompt")) {
    const maxChars = surface === "comment" ? Number(config.comments.maxChars) || 280 : Number(config.dms.maxChars) || 700;
    console.log("\n--- system prompt ------------------------------------------------------");
    // The same lookup the real call makes, with the same media id, so what is
    // printed here is what the model would be sent — including nothing at all
    // when the message matches no article well enough.
    const pages = aiLib.reference(text, { config, rulesConfig, mediaId: surface === "dm" ? "" : mediaId });
    console.log(
      aiLib.systemPrompt(config, {
        surface,
        maxChars,
        forbidden: aiLib.liveKeywords(rulesConfig),
        language: aiLib.languageInstruction(text),
        reference: pages,
      })
    );
    console.log("------------------------------------------------------------------------");
    console.log(pages.length ? `[${pages.length} page(s) retrieved, ${pages.join("\n").length} chars]` : "[no page matched well enough — the prompt above is exactly Plan A]");
    console.log("------------------------------------------------------------------------");
  }

  // Checked here and not at the top so that --prompt still works with no key at
  // all: reading the assembled prompt is most of the value and costs nothing.
  if (!ai.configured()) {
    console.error("\nNo OPENAI_API_KEY — that is the kill switch, and with it unset the fallback is off.");
    process.exit(2);
  }

  console.log(`\n> ${text}\n`);

  const reply =
    surface === "comment"
      ? await ai.replyToComment({ text, username, config, rulesConfig, mediaId })
      : await ai.replyToDm({ text, username, history: [], config, rulesConfig });

  if (!reply) {
    console.log("(no reply — the model chose SKIP, or a guard above suppressed it)");
    return;
  }

  console.log(reply);
  console.log(`\n[${reply.length} chars]`);
}

main().catch((err) => {
  console.error("failed:", err && err.code, err && err.message);
  process.exit(1);
});
