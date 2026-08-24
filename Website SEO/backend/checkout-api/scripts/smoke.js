#!/usr/bin/env node
/**
 * A real transaction against Thawani UAT, end to end, from this machine.
 *
 * Boots the service in-process, posts the exact body the checkout page builds,
 * and prints back the redirect URL the buyer would be sent to plus everything
 * we told Thawani about them. Then reads the session back the way
 * /en/order-v4/ does, which should say `unpaid` until someone actually pays.
 *
 *   npm run smoke                      # the deposit, the common case
 *   npm run smoke -- full stack        # pay in full for the Operator Stack
 *
 * Finish it by hand: open the printed URL, pay with a Thawani test card, and
 * run `npm run smoke -- status <session_id>` to watch it turn paid.
 */
process.env.ALLOWED_ORIGINS = process.env.ALLOWED_ORIGINS || "https://aiprofitlab.io";

const app = require("../server");
const pricing = require("../lib/pricing");
const thawani = require("../lib/thawani");

const args = process.argv.slice(2);

const BASKETS = {
  base: ["website"],
  stack: ["website", "dashboard", "autopilot"],
  everything: ["website", "dashboard", "autopilot", "desk"],
};

async function main() {
  const server = app.listen(0);
  await new Promise((r) => server.once("listening", r));
  const origin = `http://127.0.0.1:${server.address().port}`;

  try {
    if (args[0] === "status") {
      const id = args[1];
      if (!id) throw new Error("usage: npm run smoke -- status <session_id>");
      const r = await fetch(`${origin}/session/${encodeURIComponent(id)}`);
      console.log(`\n  GET /session/${id}  ->  ${r.status}`);
      console.log("  " + JSON.stringify(await r.json(), null, 2).replace(/\n/g, "\n  "));
      return;
    }

    const plan = args[0] || "deposit";
    const items = BASKETS[args[1] || "stack"] || BASKETS.stack;
    const q = pricing.quote(items, plan);

    const body = {
      reference: null, // let the server mint one, like a first-time buyer
      items,
      plan,
      founding: pricing.CATALOG.founding,
      currency: pricing.CATALOG.currency,
      quoted_due: q.due,
      quoted_total: q.total,
      customer: {
        name: "Khalid Al Balushi",
        business: "Gulf Lotus Trading LLC",
        email: "khalid@gulflotus.om",
        whatsapp: "+968 9123 4567",
        cr: "1234567",
        city: "Muscat",
        notes: "Smoke test — not a real order.",
      },
      page: "/en/checkout-v4/?plan=" + plan,
    };

    const cfg = thawani.config();
    console.log(`\n  ${cfg.base}  (${cfg.live ? "LIVE — REAL MONEY" : "uat"})`);
    console.log(`  ${q.plan.label}: ${pricing.money(q.due)} due now of ${pricing.money(q.total)}`);
    console.log("\n  products ->");
    for (const l of thawani.lineItems(q, pricing.CATALOG)) {
      console.log(`    ${l.name.padEnd(34)} ${String(l.unit_amount).padStart(9)} baisa x${l.quantity}`);
    }

    const res = await fetch(`${origin}/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Origin: "https://aiprofitlab.io" },
      body: JSON.stringify(body),
    });
    const out = await res.json();

    console.log(`\n  POST /session  ->  ${res.status}`);
    console.log("  " + JSON.stringify(out, null, 2).replace(/\n/g, "\n  "));

    if (!res.ok) {
      console.log("\n  The page would show its offline handover here and say nothing was charged.\n");
      process.exitCode = 1;
      return;
    }

    console.log("\n  metadata Thawani now holds against this transaction ->");
    const meta = thawani.metadata({
      reference: out.reference,
      customer: body.customer,
      quote: q,
      items: q.items.map((i) => i.id),
      priceColumn: pricing.CATALOG.founding ? "founding" : "standard",
    });
    for (const [k, v] of Object.entries(meta)) console.log(`    ${k.padEnd(20)} ${v}`);

    const check = await fetch(`${origin}/session/${encodeURIComponent(out.session_id)}`);
    console.log(`\n  GET /session/${out.session_id}  ->  ${check.status}`);
    console.log("  " + JSON.stringify(await check.json(), null, 2).replace(/\n/g, "\n  "));

    console.log(`\n  Pay it with a Thawani test card:\n    ${out.redirect_url}`);
    console.log(`  Then:  npm run smoke -- status ${out.session_id}\n`);
  } finally {
    server.close();
  }
}

main().catch((err) => {
  console.error("\n  SMOKE FAILED:", err && err.message, "\n");
  process.exitCode = 1;
});
