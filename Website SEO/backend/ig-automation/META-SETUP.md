# The Meta side

**Start this first.** The code is done; this is the critical path. Meta advertises
around 20 days for App Review, and none of it can be shortened by writing more
software.

## Why there is a gate at all

Meta's documentation is explicit on two points:

> "Advanced Access is required to receive `comments` and `live_comments` webhook notifications."

> "Apps must be set to Live in the App Dashboard to receive webhook notifications."

So the ManyChat-style trigger does **not** work in Development mode, not even on
your own account. Standard Access lets you call the API for accounts with a role
on your app, but the `comments` *webhook* is gated separately. Advanced Access
means Business Verification **and** App Review.

Everything except the live trigger can be tested before then — see
"Verification" in `README.md`.

---

## Checklist

### 1. Instagram account
- [ ] Switched to **Professional** (Business or Creator). A personal account
      cannot use this API at all.

### 2. The app
- [ ] Meta App Dashboard → **Create App**
- [ ] Add the **Instagram** product, using **Instagram API with Instagram Login**.
      This is the current path and needs no linked Facebook Page. (The old Basic
      Display API was sunset in September 2025 — ignore any tutorial that uses it.)
- [ ] Note the **App Secret** (Settings → Basic). This is `META_APP_SECRET`.

### 3. Business Verification
- [ ] Verify **Lotus Gulf International, CR 1570092**.
- [ ] Upload a document showing the business name **and** the registered address
      **on the same page**. A name on one page and an address on another is the
      usual rejection.
- [ ] Arabic documents are accepted without translation.
- [ ] Typically 1–5 business days.

### 4. Add yourself as a tester
- [ ] Add your Instagram account as an **Instagram Tester** and accept the
      invitation from the Instagram app. This is what lets you exercise the API
      against real data while review is pending.

### 5. App Review assets
- [x] Privacy policy — live at `https://aiprofitlab.io/privacy.html`
- [x] Terms — live at `https://aiprofitlab.io/terms.html`
- [x] **Data deletion** — Meta requires either a callback URL or documented
      instructions. Added as a section in `privacy.html`, reachable at
      `https://aiprofitlab.io/privacy.html#data-deletion`. Paste that URL into
      the "Data Deletion Instructions URL" field.
- [ ] **Screencast of the full flow.** Reviewers reject submissions that skip the
      consent screen, so record, in one take:
      1. the Instagram OAuth consent screen, with the permissions visible
      2. a comment being posted with the keyword
      3. the DM arriving
      4. the public reply appearing
      5. the lead landing in the sheet

### 6. Request Advanced Access
- [ ] `instagram_business_basic`
- [ ] `instagram_business_manage_comments`
- [ ] `instagram_business_manage_messages`

### 7. Go Live
- [ ] Flip the app to **Live** in the dashboard. Webhooks are not delivered
      otherwise, even with Advanced Access granted.

### 8. Webhook
- [ ] Callback URL `https://hooks.aiprofitlab.io/ig`, verify token = your
      `IG_VERIFY_TOKEN`. **This part works before Advanced Access** — do it early
      so the handshake is proven.
- [ ] Subscribe to `comments` and `messages`.

---

## Constraints the design already accounts for

These are Meta's rules, not choices. They are listed because they shape what the
automation can promise, and it is worth knowing them before writing campaign copy.

| Constraint | What it means for you |
|---|---|
| **One** private reply per comment, ever | The first DM must carry the whole payload. No "hi!" followed by the link — the service sends text and link as a single message for exactly this reason. |
| Private reply window is **7 days** from the comment | Old comments cannot be back-filled. A campaign cannot be switched on retroactively. |
| Replying again needs them to message first, within **24h** | Email capture only works if they answer the DM, and only for a day. |
| Long-lived tokens expire in **60 days** | Handled by `ig-token-refresh.timer`. Do not disable it. |
| Instagram must be Professional | Personal accounts are not eligible. |

## After approval

Work through "After Advanced Access" in `README.md` — comment from a second
account, confirm the DM, the public reply and the CRM row, then comment again to
prove the dedupe holds.
