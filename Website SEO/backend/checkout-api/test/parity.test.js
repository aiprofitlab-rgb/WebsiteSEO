/**
 * The port against the original.
 *
 * lib/pricing.js is a hand-written port of pay.quote(). A port is a second copy
 * of an arithmetic, and a second copy of an arithmetic drifts — silently, and in
 * the direction of charging the wrong number, because both sides agreeing is the
 * only thing the runtime mismatch check can see.
 *
 * So this asks pay.py directly. Every basket x every plan, both engines, all
 * seven money fields. It needs python3 and the repo checked out; where neither
 * is true (a Cloud Run build) it skips rather than fails.
 */
const test = require("node:test");
const assert = require("node:assert");
const { execFileSync } = require("node:child_process");
const path = require("node:path");
const fs = require("node:fs");

const pricing = require("../lib/pricing");

const PAY_DIR = path.resolve(__dirname, "..", "..", "..", "tools", "v4");
const available = fs.existsSync(path.join(PAY_DIR, "pay.py"));

const SCRIPT = `
import itertools, json, sys
sys.path.insert(0, ${JSON.stringify(PAY_DIR)})
import pay

optional = [i["id"] for i in pay.CATALOG if not i["required"]]
out = []
for n in range(len(optional) + 1):
    for combo in itertools.combinations(optional, n):
        for p in pay.PLANS:
            items = [pay.BASE_ID] + list(combo)
            q = pay.quote(items, p["id"])
            out.append({
                "items": items, "plan": p["id"],
                "parts": q["parts"], "subtotal": q["subtotal"], "saving": q["saving"],
                "surcharge": q["surcharge"], "total": q["total"], "due": q["due"],
                "balance": q["balance"], "later": q["later"], "bundled": q["bundled"],
            })
print(json.dumps(out))
`;

test("every basket prices identically in pay.py and lib/pricing.js", { skip: available ? false : "pay.py not reachable" }, () => {
  const raw = execFileSync("python3", ["-c", SCRIPT], { encoding: "utf8", cwd: PAY_DIR });
  const cases = JSON.parse(raw);
  assert.ok(cases.length >= 32, `expected the full cross-product, got ${cases.length}`);

  for (const c of cases) {
    const q = pricing.quote(c.items, c.plan);
    for (const field of ["parts", "subtotal", "saving", "surcharge", "total", "due", "balance", "later"]) {
      assert.equal(q[field], c[field], `${c.plan} / ${c.items.join("+")} -> ${field}`);
    }
    assert.equal(q.bundled, c.bundled, `${c.plan} / ${c.items.join("+")} -> bundled`);
  }
});

test("catalog.json is what pay.py exports today", { skip: available ? false : "pay.py not reachable" }, () => {
  const exporter = path.join(PAY_DIR, "export_catalog.py");
  const fresh = execFileSync("python3", ["-c", `
import json, sys
sys.path.insert(0, ${JSON.stringify(PAY_DIR)})
import export_catalog
print(json.dumps(export_catalog.catalog(), ensure_ascii=False))
`], { encoding: "utf8", cwd: PAY_DIR });
  assert.ok(fs.existsSync(exporter));
  assert.deepEqual(JSON.parse(fresh), pricing.CATALOG, "run tools/v4/export_catalog.py — catalog.json is stale");
});
