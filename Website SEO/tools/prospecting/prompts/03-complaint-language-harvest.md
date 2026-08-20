# Track 3 — Turn negative reviews into real buyer language

DEPENDS ON: `out/prospecting/oman-negative-reviews.csv` (run the miner first).

---

Context: I run AI Profit Lab (aiprofitlab.io), an AI automation + web agency in
Muscat, Oman. My competitor research lives in `.agents/competitors/` — read
`README.md` and `_us.yml` there before you write anything. That directory has
hard rules I want followed exactly:

- Every competitor fact lives in exactly one `.yml` file
- `confidence:` is `high` (they publish it), `medium` (inferred from their site),
  or `low` (press/third-party derived)
- Never publish a `low`-confidence fact
- Never invent a complaint, a client or a price

The README itself flags this gap: *"When a prospect mentions a competitor,
capture what they said in that competitor's `common_complaints`. Real buyer
language is worth more than anything on their website."* Right now every
`common_complaints:` field in that directory is empty `[]`.

I have `out/prospecting/oman-negative-reviews.csv` — real 1-to-3-star Google
reviews of Omani web and digital agencies, with the review text, star rating,
date and which agency it was left on.

What I want:

1. Read the CSV. Cluster the complaints into recurring themes in the reviewers'
   own words — not your paraphrase. Likely axes: missed deadlines, going silent
   after payment, refusing handover of domain/hosting/source, charging for fixes
   to their own bugs, template work sold as custom, no Arabic support, no
   post-launch support. Let the data decide; do not force these categories.
2. Count how many reviews support each theme and quote 2-3 verbatim examples per
   theme, each with the agency name and date. Arabic reviews: keep the original
   and add a translation, clearly marked.
3. IMPORTANT — do not stuff these into the existing competitor YAMLs. The
   reviews are of *web design agencies*, which are a different set of companies
   from the AI-automation competitors already tracked there (QwicLink, Nuqta,
   4Ys, WIYA). Cross-contaminating those files would put unverifiable claims
   against named competitors. Instead create a new file
   `.agents/competitors/web-agency-complaints.yml` following the directory's
   existing field conventions, with `verified:`, `confidence:` and the source
   CSV named.
4. Where a complaint lands on an agency that IS already tracked in that
   directory, and only then, add it to that competitor's own
   `common_complaints:` with the review date and star rating as the source.
5. Then tell me what this changes about how I sell. Specifically: which of these
   fears should my website answer directly, and where. Be concrete — name the
   page and the section.

Constraints from my own repo I want respected: I publish no named clients or
testimonials, which is my biggest credibility gap. Do not write copy implying I
have either. Do not repeat the stale "live in 14-30 days" claim — the live
services page says 3-6 / 6-12 / 10-14 weeks and that is correct.

If the CSV is thin (Google caps reviews at 5 per business, so it may be), say so
plainly and tell me what the sample can and cannot support. A theme backed by
three reviews is a hypothesis, not a finding — label it that way.
