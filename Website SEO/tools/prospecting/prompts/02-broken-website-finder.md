# Track 2 — Find Omani businesses with broken or absent websites

NO DEPENDENCY. Run this one first if you only run one. Needs a
`GOOGLE_MAPS_API_KEY` with Places API (New) enabled and billing on.

---

Context: I run AI Profit Lab (aiprofitlab.io), an AI automation + web agency in
Muscat, Oman. I sell a "Website with built-in AI" at OMR 800 one-time + OMR
100/month optional maintenance. Verified pricing and positioning are in
`.agents/competitors/_us.yml` — read it, don't trust memory.

The thesis: instead of chasing people who left bad reviews of other agencies
(anonymous, uncontactable, complaining about something that happened years ago),
find Omani businesses whose website is *currently* absent or visibly broken.
They are contactable — the phone is right there on their Google listing — the
problem is provable in one screenshot, and it maps straight onto my OMR 800
product.

Build me `tools/prospecting/broken_site_finder.py`. There is a working sibling
script at `tools/prospecting/gmaps_review_mining.py` — read it first and match
its conventions: stdlib only, no pip install, `--dry-run`, and a confirmation
gate before any metered API phase.

What it should do:

1. Sweep Omani SME categories that live or die on a website — restaurants,
   clinics, dental, gyms, salons, law firms, real estate, car rental, tourism
   and travel, contractors, private schools, trading companies — across Muscat,
   Al Khuwair, Ruwi, Seeb, Sohar, Salalah, Nizwa, Sur, Barka.
2. IMPORTANT COST DESIGN. Put `places.websiteUri` and
   `places.nationalPhoneNumber` directly in the **Text Search** field mask. That
   returns the website for up to 20 businesses per single billed call, instead
   of one metered Place Details call per business. Website and phone are
   Enterprise-tier fields, so the call bills at Text Search Enterprise, which
   has a 1,000-call/month free allowance — roughly 20,000 businesses for free.
   Do NOT loop Place Details over every business; that is the expensive shape
   and it will blow through the cap.
3. Bucket each business:
   - NO_WEBSITE — `websiteUri` absent. The cleanest signal.
   - SOCIAL_ONLY — the "website" is a facebook.com / instagram.com link
   - DEAD — DNS failure, connection refused, 4xx/5xx
   - NO_SSL — http:// only, or an invalid certificate
   - PLACEHOLDER — parked domain, "coming soon", default host page
   - NOT_MOBILE — no viewport meta tag
   - STALE — copyright year 2 or more years old
   - OK — none of the above; exclude from the lead list
4. Health-check with a HEAD then a small GET, short timeout, and a courtesy
   pause. Never hammer a prospect's server.
5. Output `out/prospecting/broken-site-leads.csv`: score, business, category,
   area, defect_bucket, evidence (status code / missing tag / year found),
   website, phone, maps_url, verified_date.

Scoring: Hot = NO_WEBSITE or DEAD, and a phone number is present. Warm =
SOCIAL_ONLY, PLACEHOLDER or NO_SSL. Cold = NOT_MOBILE or STALE only.

Then run it and give me the results. Report the real counts per bucket — if a
bucket is empty, say so rather than padding it.

Rules: this is my own outreach list, not a product to resell. Public business
contact channels only. Report what the run actually found, including failures.
