# App Review — the written answers

Meta replaced the old "upload a screencast and a paragraph" form with a staged
questionnaire: **Verification → App settings → Allowed usage → Data handling →
Reviewer instructions**. The screencast is still required; it is now one item
inside "Allowed usage" rather than the whole submission.

Everything below is copy-paste text, checked against what the code actually does.
Two placeholders to fill: `@HANDLE` (the connected Instagram professional account)
and `[mm:ss]` (timestamps in your recording).

---

## 0. Two things to fix before you answer anything

### Drop **Human Agent** from the submission

The Human Agent feature lets an app send messages with the `human_agent` tag up
to 7 days after a user's message. **This app never sets that tag.** It sends
exactly two kinds of message, both inside Meta's standard windows:

- one private reply per comment (`recipient: { comment_id }`), within 7 days of
  the comment — `lib/ig.js` `privateReply`
- automated replies inside the standard 24-hour window after the person messages
  us — `lib/ig.js` `sendText`

A permission the screencast cannot demonstrate is a rejection. Replying to a DM
by hand in the Instagram app needs no permission at all, so nothing is lost.
Use **edit your submission** on the Allowed usage page to remove it.

### Confirm `instagram_business_manage_comments` is still in the submission

The Allowed usage page lists `instagram_business_basic` and
`instagram_business_manage_messages`. Without `manage_comments` there is no
`comments` webhook and no public reply — that is the entire trigger. If it is
missing, add it before submitting.

---

## 1. instagram_business_basic

> Describe how your app uses this permission or feature

```
AI Profit Lab is a comment-to-DM automation that runs on our own Instagram
professional account (@HANDLE). It is a single-account business tool operated by
the account owner, not a consumer app or a multi-tenant service. The account is
connected through Instagram Business Login at
https://hooks.aiprofitlab.io/ig/oauth/start.

We use instagram_business_basic for three things:

1. Identify the connected account. Immediately after login we call
   GET /me?fields=id,username once, to learn our own Instagram user ID and
   username. This is what lets the automation tell its own comments apart from a
   follower's. Our public reply under a comment is itself a comment, and Meta
   delivers it back to us on the comments webhook; without knowing our own ID the
   service would match its own reply and answer itself in a loop under a real
   customer's post.

2. List our own posts and reels in the admin panel. GET /me/media with fields
   id, caption, media_type, media_url, thumbnail_url, permalink, timestamp
   populates a post picker, so the owner can scope a keyword to particular posts
   — the word "guide" can send a different link under two different reels.

3. Read the permalink of the post a comment came from
   (GET /{media-id}?fields=permalink), so the lead record shows which post
   produced the lead.

It is necessary because the automation cannot safely act without knowing which
account it is, and because campaigns are configured against posts the owner can
recognise rather than raw media IDs.

We read only our own account's profile and media. We do not read any other
account's profile, media, insights or followers.

Screencast: [mm:ss] the Instagram Business Login consent screen and the
"Connected as @HANDLE" page that follows it (GET /me); [mm:ss] the admin panel's
post picker listing our real posts and reels (GET /me/media).
```

---

## 2. instagram_business_manage_comments

> Describe how your app uses this permission or feature

```
We use instagram_business_manage_comments to receive the comments webhook for our
own account's posts and to post one public reply under a comment that matched a
keyword.

Flow: a follower comments a keyword the owner configured — for example "price",
"demo", "guide", or the Arabic "سعر" — under one of our posts or reels. Meta
delivers the comment on the comments webhook. We verify the X-Hub-Signature-256
header, read the comment text and the commenter's username and ID, and check the
text against the keyword rules configured for that post. If it matches, we send
the follower a private reply and then post one short public reply under their
comment: "Sent! Check your DMs 📩"
(POST /{comment-id}/replies).

The public reply exists so the follower — and everyone else reading the thread —
knows the answer is already on its way, instead of wondering whether the business
saw the comment. It is posted only after the DM has actually been delivered; if
the DM fails, no public reply is posted, because "check your DMs" under a comment
that got no DM is worse than silence.

We reply once per comment and never more: comment IDs are claimed atomically in a
local database, so a redelivered webhook cannot produce a second reply. A circuit
breaker caps the account at 12 replies per post per hour and 40 per hour overall.

We act only on our own account's posts. We do not comment on anyone else's posts,
and we do not moderate, hide, or delete comments.

Screencast: [mm:ss] a comment posted with the keyword from a second account, and
[mm:ss] the public reply appearing underneath it.
```

---

## 3. instagram_business_manage_messages

> Describe how your app uses this permission or feature

```
We use instagram_business_manage_messages to answer a follower who has commented a
keyword on our own post, and to receive their reply.

1. Private reply to a comment. When a comment matches a configured keyword we send
   exactly one message via POST /{ig-user-id}/messages with
   recipient: { comment_id }. That message carries what the person asked for —
   a link to our pricing page, our live demos, or a PDF the owner uploaded in the
   admin panel. Meta allows one private reply per comment and a 7-day window, so
   the whole answer is sent as a single message; there is no follow-up.

2. Optional email capture, inside the standard 24-hour window. Some rules invite
   the person to reply with their email address to receive a PDF. If they do
   reply, we receive the messages webhook, extract the email from their text, and
   send one confirmation via POST /{ig-user-id}/messages with recipient: { id }.
   If their reply contains no email address we send exactly one clarification
   ("that doesn't look like an email") and then stop. There is no nagging, no
   second prompt, and the state expires with Meta's 24-hour window.

We only message a person who has first commented on our post or messaged us. We
send no promotional broadcasts, we never message a person who has not contacted
us, we use no message tags, and every send is inside Meta's standard windows. We
ignore echoes of our own outbound messages.

Data received and stored: the sender's Instagram-scoped user ID, their username,
the text of the comment or message they sent us, the comment and media IDs, and
an email address if they volunteer one. It is stored in a private Google Sheet
used as our CRM, and in a local database that keeps the deduplication set and the
24-hour conversation state. Anyone can have all of it deleted within 30 days —
https://aiprofitlab.io/privacy/#data-deletion — and can revoke our access from
Instagram Settings at any time.

Value to the person: a follower who comments at 11pm gets the exact link they
asked for in seconds, rather than "DM sent!" from a business that replies the
next afternoon.

Screencast: [mm:ss] the DM arriving on the follower's phone; [mm:ss] the follower
replying with an email address and receiving the confirmation.
```

---

## 4. Data handling

### processor-0 — "Do you have data processors or service providers…?"

**Yes.** Then list:

```
Hostinger International Ltd — virtual private server hosting. The webhook service
and its local state database run on our VPS with this provider.

Google LLC (Google Sheets API) — our lead ledger. The row for each lead holds the
commenter's Instagram username and user ID, the comment ID, the media ID, the
comment text, and an email address if the person volunteered one.

Resend, Inc. — transactional email for operational alerts to the account owner.
It receives Platform Data only in one edge case: if the anti-loop circuit breaker
trips, the alert email includes the comment ID and up to 200 characters of the
comment text.
```

If any of the three is not accepted as a name, use the plain legal name only —
reviewers reject long explanations here, but they do reject missing processors too,
and all three genuinely touch the data.

### responsible-1 — "Who is the person or entity responsible for all Platform Data?"

```
Lotus Gulf International
Commercial Registration 1570092
South Al Khuwair, Bousher, Muscat, Sultanate of Oman
Trading as: AI Profit Lab
Contact: hello@aiprofitlab.io
```

This must match the entity that passed Business Verification, exactly.

### The questions that usually follow on the same page

| Question | Answer |
|---|---|
| Do you sell, license or share Platform Data? | No |
| Do you use Platform Data for advertising or ad targeting? | No |
| Do you transfer Platform Data outside your organisation? | Only to the processors listed above, under their terms |
| Do you have a data deletion process? | Yes — https://aiprofitlab.io/privacy/#data-deletion, honoured within 30 days |
| Data retention | Comment/lead records are kept while we are in contact and up to 2 years after the last exchange, then deleted. The 24-hour conversation state expires automatically. |
| Security measures | HTTPS everywhere; every webhook payload verified against X-Hub-Signature-256 and refused if unsigned; appsecret_proof on every outbound Graph call; access token stored outside the web root on the server with restricted file permissions; admin panel behind a password with per-IP lockout |
| Do you have a privacy policy? | https://aiprofitlab.io/privacy/ |

---

## 5. Reviewer instructions (the last step)

```
This app automates our own Instagram professional account, @HANDLE. There is no
sign-up and no reviewer account is needed to see the login flow.

To see the Instagram Business Login consent screen and confirm the app loads and
can be tested externally, open:

  https://hooks.aiprofitlab.io/ig/oauth/start

Log in with any Instagram professional account. You will see the consent screen
listing instagram_business_basic, instagram_business_manage_comments and
instagram_business_manage_messages, and then a page confirming which account
connected.

This page stores nothing. It exchanges the code, asks Meta which account it
belongs to, shows you the answer, and discards the token. Connecting your own
account does not change or affect the live automation.

The end-to-end behaviour cannot be reproduced by a reviewer from outside, because
the comments webhook requires Advanced Access, which is what this submission
requests. The screencast shows the full flow on our own account: a follower
comments a keyword, receives a DM with the link, a public reply appears under the
comment, and the lead is recorded.
```

---

## 6. The screencast

Your existing recording is probably still usable — the flow has not changed, only
the form around it. Two things to check:

- **It must be an uploaded file, not a Loom link.** MP4 or MOV. Export the Loom
  as MP4 and upload the same file to each permission's field.
- **The consent screen must be in it.** A screencast that starts after login is
  the most common rejection. `https://hooks.aiprofitlab.io/ig/oauth/start` is
  shot 1.

Give each permission its own timestamp in the description, as marked above.
