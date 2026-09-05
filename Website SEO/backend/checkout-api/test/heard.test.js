/**
 * "How did you hear about us?" on its way into the ledger's Notes column.
 */
const test = require("node:test");
const assert = require("node:assert");

const heard = require("../lib/heard");
const thawani = require("../lib/thawani");
const pricing = require("../lib/pricing");

test("an id becomes the English label, in either language", () => {
  // The Arabic checkout posts "flyer" too — that is the entire point of an id.
  assert.equal(heard.line("flyer", ""), "Heard about us: A printed flyer");
  assert.equal(heard.line("referral", ""), "Heard about us: Someone recommended you");
});

test("the follow-up answer rides on the same line", () => {
  assert.equal(
    heard.line("referral", "Ahmed at Gulf Lotus"),
    "Heard about us: Someone recommended you — Ahmed at Gulf Lotus"
  );
});

test("an id this service has never seen is written through, not dropped", () => {
  // A page can be redeployed with a new option before the service is. An answer
  // nobody has a label for still beats no answer at all.
  assert.equal(heard.line("tiktok", ""), "Heard about us: tiktok");
});

test("no answer produces no line at all, never a bare prefix", () => {
  assert.equal(heard.line("", ""), "");
  assert.equal(heard.line(null, "someone told me"), "");
  assert.equal(heard.line(undefined, undefined), "");
});

test("the line stays one line whatever was pasted into the box", () => {
  const line = heard.line("other", "saw it at\nthe\r\nexhibition");
  assert.ok(!line.includes("\n"), "a newline would break the cell's shape");
  assert.equal(line, "Heard about us: Somewhere else — saw it at the exhibition");
});

test("the buyer's own note is kept, under the answer", () => {
  const notes = heard.prepend("We quote by WhatsApp all day.", "flyer", "");
  assert.equal(notes, "Heard about us: A printed flyer\n\nWe quote by WhatsApp all day.");
});

test("a buyer who wrote nothing leaves no blank lines behind", () => {
  assert.equal(heard.prepend("", "google", ""), "Heard about us: Google search");
  assert.equal(heard.prepend("   ", "google", ""), "Heard about us: Google search");
});

test("a note from a page that never asked the question survives untouched", () => {
  // The old checkout is cached in somebody's tab. It must still be able to pay,
  // and what it does send must still land.
  assert.equal(heard.prepend("Call me after 4pm.", "", ""), "Call me after 4pm.");
});

test("the Notes cell can never open with a character Sheets reads as a formula", () => {
  // lib/ledger.js writes USER_ENTERED. The prefix is what makes this column
  // safe: "=1+1" typed into the follow-up box lands mid-string, as text.
  const notes = heard.prepend("=1+1", "other", "=HYPERLINK(\"http://x\")");
  assert.ok(notes.startsWith("Heard about us: "));
});

test("the answer still does not reach the payment processor", () => {
  // It now lives inside customer.notes, which metadata() has always excluded —
  // asserted here as well because the reason it is excluded has changed shape.
  const q = pricing.quote(["website"], "deposit");
  const m = thawani.metadata({
    reference: "APL-260905-KX7M",
    customer: {
      name: "Khalid Al Balushi",
      business: "Gulf Lotus Trading LLC",
      email: "khalid@gulflotus.om",
      whatsapp: "+968 9123 4567",
      cr: "",
      city: "Muscat",
      notes: heard.prepend("", "referral", "Ahmed at Gulf Lotus"),
      heardAbout: "referral",
      heardDetail: "Ahmed at Gulf Lotus",
    },
    quote: q,
    items: q.items.map((i) => i.id),
  });
  const blob = JSON.stringify(m);
  assert.ok(!blob.includes("Ahmed"), "who referred them is nobody's business but ours");
  assert.ok(!blob.includes("referral"));
});

test("every option the checkout renders has a label here", () => {
  // The page's list lives in tools/v4/page_checkout.py:HEARD. These are the ids
  // it renders today; a new one added there without a label here degrades to
  // the raw id (see above), which is survivable but reads badly in the sheet.
  const rendered = [
    "flyer", "google", "ai", "instagram", "linkedin",
    "whatsapp", "referral", "inperson", "other",
  ];
  for (const id of rendered) {
    assert.ok(heard.LABELS[id], `no label for "${id}"`);
  }
});
