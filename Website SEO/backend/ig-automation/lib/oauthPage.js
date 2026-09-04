/**
 * The page a reviewer sees a second after they tap Allow.
 *
 * This is the one screen in the service built to be FILMED, so it is sized for
 * a 1080p screencast rather than for a desk: large type, one idea per line, and
 * the granted permissions listed in full, because that list is what the reviewer
 * is checking against the submission. Palette matches admin/public/app.css so
 * the video does not look like it wandered into a different product.
 *
 * Self-contained — inline CSS, no fonts, no scripts, no requests. A spinner or
 * a webfont that has not loaded is not something you want in the take.
 */

const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const CSS = `
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
    padding: 32px 20px; background: #f1efe8; color: #232b26;
    font: 16px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  .card {
    width: 100%; max-width: 560px; background: #faf8f2; border: 1px solid #ded8c8;
    border-radius: 16px; padding: 40px; box-shadow: 0 12px 40px rgba(35, 43, 38, .08);
  }
  .mark {
    width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 34px; font-weight: 700; color: #faf8f2; margin-bottom: 24px;
  }
  .ok   { background: #0f6e56; }
  .bad  { background: #a6431f; }
  h1 { margin: 0 0 8px; font-size: 30px; line-height: 1.2; letter-spacing: -.02em; }
  .lede { margin: 0 0 28px; font-size: 17px; color: #5a665d; }
  .label {
    margin: 0 0 12px; font-size: 12px; font-weight: 700; letter-spacing: .09em;
    text-transform: uppercase; color: #9f9683;
  }
  ul { list-style: none; margin: 0 0 28px; padding: 0; }
  li {
    display: flex; gap: 12px; align-items: baseline; padding: 11px 0;
    border-top: 1px solid #ded8c8; font-size: 16px;
  }
  li:last-child { border-bottom: 1px solid #ded8c8; }
  .tick { color: #0f6e56; font-weight: 700; }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 15px; }
  .note {
    margin: 0; padding: 16px 18px; border-radius: 10px; background: #f1efe8;
    border: 1px solid #ded8c8; font-size: 14.5px; color: #5a665d;
  }
  .note.warn { background: #f6ecd8; border-color: #e2cfa5; color: #7a5310; }
  .note strong { color: #232b26; }
  .foot { margin: 28px 0 0; font-size: 13.5px; color: #9f9683; }
`;

const shell = (title, body) => `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>${esc(title)}</title>
<style>${CSS}</style>
</head><body><main class="card">${body}</main></body></html>`;

/**
 * @param {object} result the shape lib/oauth.js `connect()` returns
 */
function success(result) {
  const { account, permissions, expiresInDays, isConfiguredAccount } = result;
  const who = account.username ? `@${account.username}` : `account ${account.id}`;

  const items = permissions
    .map((p) => `<li><span class="tick" aria-hidden="true">&#10003;</span><code>${esc(p)}</code></li>`)
    .join("");

  // Said out loud on the page rather than left implied, because it is the
  // question a reviewer completing this flow with their own account would
  // otherwise have to guess the answer to.
  const storage = isConfiguredAccount
    ? `<p class="note">This is the account AI Profit Lab is configured to run as. <strong>The access token was not saved</strong> — this page confirms the login and discards it. The service's own token is rotated by a scheduled job.</p>`
    : `<p class="note warn"><strong>Nothing was stored.</strong> This page confirms Instagram issued a valid access token for ${esc(who)} with the permissions above, then discards it. AI Profit Lab does not post to, read from, or retain data for any account other than the one it is configured for.</p>`;

  return shell(
    `Connected as ${who}`,
    `<div class="mark ok" aria-hidden="true">&#10003;</div>
     <h1>Connected as ${esc(who)}</h1>
     <p class="lede">Instagram Business Login completed successfully${
       expiresInDays ? `. The access token is valid for ${expiresInDays} days` : ""
     }.</p>
     <p class="label">Permissions granted</p>
     <ul>${items}</ul>
     ${storage}
     <p class="foot">AI Profit Lab &middot; Lotus Gulf International &middot; <a href="https://aiprofitlab.io/privacy/">Privacy</a> &middot; <a href="https://aiprofitlab.io/privacy/#data-deletion">Delete my data</a></p>`
  );
}

/**
 * The failure page. Shows Meta's own wording — a reviewer who hits an error is
 * going to screenshot this, and "something went wrong" gives them nothing to
 * put in the rejection, which means the rejection says nothing useful back.
 */
function failure({ title = "Could not complete sign-in", detail = "", retry = true } = {}) {
  return shell(
    title,
    `<div class="mark bad" aria-hidden="true">&#33;</div>
     <h1>${esc(title)}</h1>
     <p class="lede">Instagram did not return a usable authorization.</p>
     ${detail ? `<p class="note"><strong>Instagram said:</strong> ${esc(detail)}</p>` : ""}
     ${retry ? `<p class="foot"><a href="/ig/oauth/start">Try again</a></p>` : ""}
     <p class="foot">AI Profit Lab &middot; <a href="https://aiprofitlab.io/privacy/">Privacy</a></p>`
  );
}

module.exports = { success, failure, _esc: esc };
