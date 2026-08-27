/**
 * Incident mail, via the same Resend sender checkout-api uses.
 *
 * There is exactly one thing here worth an email: the token stopped refreshing.
 * That failure is invisible — the webhook keeps arriving and every Graph call
 * quietly 190s — and it has a 60-day fuse. Everything else belongs in the log.
 *
 * No RESEND_API_KEY? Log and continue. Alerting must never be the reason the
 * automation itself falls over.
 */

const { Resend } = require("resend");

const FROM = "AI Profit Lab <hello@aiprofitlab.io>";
const OWNER = process.env.OWNER_EMAIL || "hello@aiprofitlab.io";

let resend = null;
function client() {
  if (!process.env.RESEND_API_KEY) return null;
  if (!resend) resend = new Resend(process.env.RESEND_API_KEY);
  return resend;
}

const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function send(payload) {
  const c = client();
  if (!c) {
    console.warn("MAIL SKIPPED (no RESEND_API_KEY):", payload.subject);
    return { skipped: true };
  }
  try {
    return await c.emails.send({ from: FROM, ...payload });
  } catch (err) {
    console.error("MAIL ERROR:", payload.subject, err && err.message);
    return { error: true };
  }
}

const shell = (inner) => `<div style="font-family:-apple-system,Segoe UI,sans-serif;font-size:15px;line-height:1.6;color:#232B26;background:#F1EFE8;padding:28px">
<div style="max-width:560px;margin:0 auto;background:#FAF8F2;border:1px solid #DAD4C4;border-radius:12px;padding:28px">
${inner}
</div></div>`;

/** The daily refresh did not work. Days left is the number that matters. */
function tokenRefreshFailed({ reason, message, daysLeft }) {
  const urgent = daysLeft != null && daysLeft <= 14;
  return send({
    to: OWNER,
    subject: `${urgent ? "URGENT — " : ""}Instagram token refresh failed (${reason})`,
    html: shell(`
<h2 style="margin:0 0 12px;font-size:19px">The Instagram token did not refresh</h2>
<p style="margin:0 0 16px">Comment automation keeps receiving webhooks, but once the token expires every DM and reply silently fails.</p>
<table style="border-collapse:collapse;font-size:14px">
<tr><td style="padding:2px 12px 2px 0;color:#5C6259">Reason</td><td style="padding:2px 0"><b>${esc(reason)}</b></td></tr>
<tr><td style="padding:2px 12px 2px 0;color:#5C6259">Meta said</td><td style="padding:2px 0"><b>${esc(message)}</b></td></tr>
<tr><td style="padding:2px 12px 2px 0;color:#5C6259">Days left</td><td style="padding:2px 0"><b>${daysLeft == null ? "unknown" : esc(daysLeft)}</b></td></tr>
</table>
<p style="margin:20px 0 0;font-size:13px;color:#5C6259">Fix: generate a fresh long-lived token in the Meta App Dashboard and write it to the token file, then <code>npm run refresh-token</code> to confirm rotation works again.</p>`),
  });
}

/** A Graph call came back with a token error during normal traffic. */
function tokenRejected({ where, message, code }) {
  return send({
    to: OWNER,
    subject: "URGENT — Instagram token rejected, DMs are not sending",
    html: shell(`
<h2 style="margin:0 0 12px;font-size:19px">Instagram rejected the access token</h2>
<p style="margin:0 0 16px">A real follower comment could not be answered. Every further comment will fail the same way until the token is replaced.</p>
<table style="border-collapse:collapse;font-size:14px">
<tr><td style="padding:2px 12px 2px 0;color:#5C6259">Where</td><td style="padding:2px 0"><b>${esc(where)}</b></td></tr>
<tr><td style="padding:2px 12px 2px 0;color:#5C6259">Code</td><td style="padding:2px 0"><b>${esc(code)}</b></td></tr>
<tr><td style="padding:2px 12px 2px 0;color:#5C6259">Message</td><td style="padding:2px 0"><b>${esc(message)}</b></td></tr>
</table>`),
  });
}

module.exports = { tokenRefreshFailed, tokenRejected, send };
