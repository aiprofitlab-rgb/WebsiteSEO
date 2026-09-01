/**
 * The price table, and the arithmetic over it.
 *
 * catalog.json is written by tools/v4/export_catalog.py straight out of
 * tools/v4/pay.py — the same table the checkout page is built from. Nothing
 * here restates a price. What IS restated is quote(), which is a line-for-line
 * port of pay.quote(), because the server has to reach the same number the
 * buyer was shown, from its own copy, without ever trusting the browser's.
 *
 * MONEY IS INTEGER BAISA THROUGHOUT. 1 OMR = 1000 baisa. Thawani's
 * `unit_amount` is an integer number of baisa and rejects decimals, so there
 * is no float in this file and no division that isn't floored.
 */

const fs = require("fs");
const path = require("path");

const CATALOG = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "catalog.json"), "utf8"));

const OMR = CATALOG.baisa;

function item(id) {
  return CATALOG.items.find((i) => i.id === id) || null;
}

function plan(id) {
  return CATALOG.plans.find((p) => p.id === id) || null;
}

/**
 * Port of pay.quote(). Same inputs, same integer arithmetic, same field names.
 *
 * There is one price per item in catalog.json and no column to choose between,
 * so a quote is fully determined by the items and the plan. The route still
 * refuses any order whose quoted figures disagree with what this recomputes.
 */
function quote(itemIds, planId) {
  const p = plan(planId);
  if (!p) throw new Error(`unknown plan: ${planId}`);

  const ids = new Set(itemIds);
  const chosen = CATALOG.items.filter((i) => ids.has(i.id) || i.required);
  const build = chosen.filter((i) => i.kind === "build");
  const monthly = chosen.filter((i) => i.kind === "monthly");

  const parts = build.reduce((sum, i) => sum + i.price, 0);
  const have = new Set(build.map((i) => i.id));

  // NOTE: mirrors pay.py exactly, including the fact that a bundled order is
  // priced at the bundle price regardless of what else is in `build`. With
  // three build items in the catalog that can never under-charge, because the
  // bundle IS all three. Add a fourth build item and both this and pay.quote()
  // need revisiting together — a divergence here would be invisible, since the
  // two agreeing is the only thing the mismatch check can see.
  const bundled = CATALOG.bundle.requires.every((r) => have.has(r));
  const subtotal = bundled ? CATALOG.bundle.price : parts;
  const saving = parts - subtotal;

  const total = subtotal + p.surcharge;

  let due;
  if (p.due === "deposit") {
    due = Math.min(CATALOG.deposit, total);
  } else if (p.due === "total") {
    due = total;
  } else if (p.due === "first") {
    // Whole-rial instalments, rounding remainder carried by the FIRST payment,
    // so the two later invoices are identical. Two floors, no float.
    const per = Math.floor(Math.floor(total / p.split) / OMR) * OMR;
    due = total - per * (p.split - 1);
  } else {
    due = 0;
  }

  return {
    items: build,
    monthly,
    bundled,
    parts,
    subtotal,
    saving,
    surcharge: p.surcharge,
    total,
    due,
    balance: total - due,
    later: p.split > 1 ? Math.floor((total - due) / (p.split - 1)) : 0,
    plan: p,
  };
}

/** Format baisa as an OMR figure — the port of pay.omr()/pay.money(). */
function omr(baisa) {
  const whole = Math.floor(Math.abs(baisa) / OMR);
  const rem = Math.abs(baisa) % OMR;
  const sign = baisa < 0 ? "-" : "";
  let s = sign + whole.toLocaleString("en-US");
  if (rem) s += "." + String(rem).padStart(3, "0");
  return s;
}

function money(baisa) {
  return `${CATALOG.currency} ${omr(baisa)}`;
}

module.exports = { CATALOG, OMR, item, plan, quote, omr, money };
