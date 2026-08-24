/**
 * Owner notification, via Resend, from the same verified sender the storefront
 * API uses.
 *
 * One rule from docs/payments-api.md §4.6: an order nobody sees is worse than
 * no order. A payment landing on a Thawani portal Nahid checks once a day is an
 * order that sat unacknowledged for a day.
 *
 * No RESEND_API_KEY? It logs and moves on. Email is a notification channel, not
 * the record — the ledger is the record.
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

const row = (k, v) => (v ? `<tr><td style="padding:2px 12px 2px 0;color:#5C6259">${esc(k)}</td><td style="padding:2px 0"><b>${esc(v)}</b></td></tr>` : "");

/** Fired the moment a session first reads back as paid. */
function paymentLanded({ reference, amountDisplay, plan, customer, sessionId, env }) {
  const tag = env === "live" ? "" : " [UAT]";
  return send({
    to: OWNER,
    subject: `${tag}Payment received — ${amountDisplay} — ${reference}`.trim(),
    html: shell(`
<h2 style="margin:0 0 12px;font-size:19px">Payment received${esc(tag)}</h2>
<p style="margin:0 0 16px;font-size:22px"><b>${esc(amountDisplay)}</b></p>
<table style="border-collapse:collapse;font-size:14px">
${row("Reference", reference)}
${row("Plan", plan)}
${row("Name", customer.name)}
${row("Business", customer.business)}
${row("Email", customer.email)}
${row("WhatsApp", customer.whatsapp)}
${row("CR", customer.cr)}
${row("City", customer.city)}
${row("Thawani session", sessionId)}
</table>
${customer.notes ? `<p style="margin:16px 0 0;padding-top:12px;border-top:1px solid #DAD4C4;font-size:14px;color:#5C6259">${esc(customer.notes)}</p>` : ""}
<p style="margin:20px 0 0;font-size:13px;color:#5C6259">Confirm it against the Thawani portal before promising anything.</p>`),
  });
}

/** Thawani refused the session; the buyer was handed to WhatsApp instead. */
function gatewayFailed({ reference, why, amountDisplay, customer }) {
  return send({
    to: OWNER,
    subject: `Checkout fell back to WhatsApp — ${reference}`,
    html: shell(`
<h2 style="margin:0 0 12px;font-size:19px">A card payment could not be started</h2>
<p style="margin:0 0 16px">The buyer saw the offline handover and was told nothing was charged. They may be about to message you.</p>
<table style="border-collapse:collapse;font-size:14px">
${row("Reference", reference)}
${row("Amount", amountDisplay)}
${row("Name", customer.name)}
${row("Business", customer.business)}
${row("WhatsApp", customer.whatsapp)}
${row("Reason", why)}
</table>`),
  });
}

module.exports = { paymentLanded, gatewayFailed };
