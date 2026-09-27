# tools/ig_pull.py — setup

Pulls @ai.profit.lab.gcc's insights and competitors' public posts into `.tmp/ig/<date>/`.
Free (Graph API has no charge, only a ~200 calls/hour limit). Read-only.

Tokens live in `~/.config/aiprofitlab/ig.env`, **outside the repo** (the repo is public):

```
IG_TOKEN=...
FB_TOKEN=...
```

```bash
mkdir -p ~/.config/aiprofitlab && touch ~/.config/aiprofitlab/ig.env && chmod 600 ~/.config/aiprofitlab/ig.env
open -e ~/.config/aiprofitlab/ig.env
```

Both tokens last 60 days. Put a reminder in the calendar to regenerate them.

## 1. IG_TOKEN (our own insights)

Uses the same Meta app as the comment automation (`backend/ig-automation/META-SETUP.md`).

1. **developers.facebook.com → the app → App Review → Permissions and Features**:
   make sure `instagram_business_manage_insights` is listed (Standard access is enough;
   no App Review needed to read your own account).
2. **App roles → Roles → Instagram Testers**: add `ai.profit.lab.gcc`, then accept the
   invite in the Instagram app (Settings → Website permissions → Apps and websites → Tester invites).
3. **Instagram → API setup with Instagram business login → Generate access tokens →
   Add account** → log in as **@ai.profit.lab.gcc** (not @nahid_aby) → copy the token
   into `IG_TOKEN=`.

The account must be a Professional (Business or Creator) account.

## 2. FB_TOKEN (competitors — optional)

Business Discovery only exists on the Facebook side, so:

1. **Link @ai.profit.lab.gcc to a Facebook Page** (Meta Business Suite → Settings →
   Instagram accounts, or the Page's Settings → Linked accounts).
2. **developers.facebook.com/tools/explorer** → pick the same app → *User Token* →
   add `instagram_basic`, `pages_show_list`, `pages_read_engagement`,
   `business_management` → *Generate Access Token* → approve with the Facebook user
   that manages the Page.
3. That token dies in an hour. Paste it into **developers.facebook.com/tools/debug/accesstoken**
   → *Extend Access Token* → copy the 60-day one into `FB_TOKEN=`.

If the permissions don't appear in the Explorer, the app lacks the Facebook-login use case:
App Dashboard → Use cases → add "Manage messaging & content on Instagram" (Facebook Login variant).

## 3. Run

```bash
python3 tools/ig_pull.py                 # everything
python3 tools/ig_pull.py --no-competitors
python3 tools/ig_pull.py --only-competitors
```

Then ask Claude to analyse `.tmp/ig/<date>/`. Claude does not run it: tokens stay with you.

## Known limits

- **Under 100 followers**, Meta returns no `follower_count` series and no demographics.
  Those errors in `errors.json` are expected until the account passes 100.
- Business Discovery works only on Business/Creator accounts; personal ones are skipped.
  Some accounts hide like counts (`likes_hidden` in the summary).
- **Paid ads are not in the API for Oman.** Meta's Ad Library API returns only EU and
  political ads, so each competitor row carries an `ad_library` link to check by hand
  (or ask Claude to go through them in the browser).
- Competitors live in `tools/ig_competitors.txt`. Take handles from the competitor's own
  website, never from a listicle.
