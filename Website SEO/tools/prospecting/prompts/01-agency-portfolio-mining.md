# Track 1 — Mine low-rated agencies' client portfolios

DEPENDS ON: `out/prospecting/oman-web-agencies.csv` (run the miner first).

---

Context: I run AI Profit Lab (aiprofitlab.io), an AI automation + web agency in
Muscat, Oman. Legal entity Lotus Gulf International. I sell a "Website with
built-in AI" at OMR 800 one-time + OMR 100/month optional maintenance, plus AI
automation plans from OMR 500 setup / 75 monthly. Verified pricing and
positioning live in `.agents/competitors/_us.yml` — read it, don't trust memory.

I have a CSV at `out/prospecting/oman-web-agencies.csv` listing web/digital
agencies in Oman with their Google Maps rating, review count, website and phone.
It was produced by `tools/prospecting/gmaps_review_mining.py`.

The thesis: an agency sitting at under 4.0 stars with a real review count is
churning clients right now. Their own portfolio/"our clients"/"case studies"
page is a public list of businesses that paid them for a website. Those
businesses are reachable (they have their own phone and email), and their site
is inspectable — unlike the anonymous reviewers, who are just display names.

What I want you to do:

1. Read the CSV. Shortlist agencies with rating < 4.0 and >= 5 reviews. If that
   is a thin list, widen to < 4.3 and say that you did.
2. For each shortlisted agency, fetch their site and find the portfolio, clients,
   projects, or case studies page. Extract every named client business.
3. Watch for these traps and note them rather than guessing:
   - Logo walls with no readable business name
   - "Clients" that are actually tools/partners/certifications the agency uses
   - JS-rendered portfolios that return nothing to a plain fetch
   - Stale portfolios listing businesses that have since closed
4. For each named client, fetch their actual website and assess it concretely:
   does it load, HTTPS, mobile viewport, obvious last-updated signals, broken
   links, "coming soon" placeholder, copyright year. Record the specific defect.
5. Find a public business contact — the company's own published phone/email or
   contact page. Public business channels only. No personal emails.
6. Output `out/prospecting/portfolio-leads.csv` with: score (Hot/Warm/Cold),
   business, source_agency, agency_rating, website, defect_found, evidence_url,
   phone, email, confidence, verified_date.

Scoring: Hot = site has a demonstrable defect I could show them in a screenshot
AND I have a contact. Warm = weak site, contact needs digging. Cold = site is
fine or client unverifiable.

Rules: cite a source URL for every claim. Never invent a client, a contact or a
defect — if you cannot verify it, mark it low confidence and say what is
missing. Do not bulk-scrape; fetch individual sites at a normal pace.

Finish with the 5 businesses you would call first and the one-line reason for
each.
