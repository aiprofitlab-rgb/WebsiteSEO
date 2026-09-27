#!/usr/bin/env python3
"""Pull Instagram insights for @ai.profit.lab.gcc, plus competitors' public posts,
into .tmp/ig/<date>/. Read-only: nothing is posted, liked or changed.

Two tokens, because Meta splits these features across two login products:

  IG_TOKEN  Instagram Login token for our own account, with the scopes
            instagram_business_basic + instagram_business_manage_insights.
            Drives everything about OUR account (graph.instagram.com).

  FB_TOKEN  Facebook Login user token with instagram_basic, pages_show_list,
            pages_read_engagement (and business_management if the Page sits in a
            Business portfolio). Only needed for competitors: Business Discovery
            exists on graph.facebook.com and nowhere else, and it requires our
            IG account to be linked to a Facebook Page. Optional: without it the
            competitor step is skipped.

Both are read from ~/.config/aiprofitlab/ig.env (KEY=value lines), outside the
repo on purpose, or from environment variables of the same name, which win.
Tokens are never printed or written: Graph error bodies do not contain them,
paging is followed by cursor rather than by Meta's `next` URL (which does), and
every message is scrubbed before it is shown anyway.

The Graph API is free; the only limit is ~200 calls/hour per account. A default
run makes roughly 30 + (posts) + (competitors) calls.

Usage:
    python3 tools/ig_pull.py                  # own account + competitors
    python3 tools/ig_pull.py --posts 100      # insights for the last 100 posts
    python3 tools/ig_pull.py --no-competitors
    python3 tools/ig_pull.py --only-competitors

Output (.tmp/ig/<YYYY-MM-DD>/):
    account.json            profile + account insights (7d, 28d, daily series)
    demographics.json       follower / engaged-audience breakdowns (needs 100+ followers)
    posts.csv               our posts, one row each, with per-post insights
    competitors.json        raw Business Discovery results
    competitors_posts.csv   every competitor post, tagged by theme
    competitors_summary.csv one row per competitor: cadence, engagement, theme mix
    errors.json             every call that failed, and why (never fatal)
"""

import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_FILE = pathlib.Path.home() / ".config" / "aiprofitlab" / "ig.env"
COMPETITORS_FILE = ROOT / "tools" / "ig_competitors.txt"

VERSION = os.environ.get("IG_API_VERSION", "v23.0")
IG_GRAPH = f"https://graph.instagram.com/{VERSION}"
FB_GRAPH = f"https://graph.facebook.com/{VERSION}"

MEDIA_FIELDS = "id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count"

# Per-post metrics differ by product type; asking for one a type lacks fails the
# whole call, so each type gets its own list and a one-by-one fallback.
POST_METRICS = {
    "REELS": ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
              "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"],
    "FEED": ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
             "profile_visits", "follows"],
}

# Account metrics read as one total over a window (metric_type=total_value).
ACCOUNT_TOTALS = ["views", "reach", "accounts_engaged", "total_interactions", "likes", "comments",
                  "shares", "saves", "replies", "profile_links_taps", "follows_and_unfollows"]
DEMOGRAPHIC_METRICS = ["follower_demographics", "engaged_audience_demographics"]
DEMOGRAPHIC_BREAKDOWNS = ["country", "city", "age", "gender"]

# Caption themes. English matches whole words; Arabic matches substrings because
# Arabic attaches prefixes (ال، ب، و، ل) that defeat word boundaries.
THEMES = {
    "website": {
        "en": ["website", "websites", "web design", "web development", "landing page", "online store",
               "e-commerce", "ecommerce", "shopify", "wordpress", "domain", "hosting", "seo", "web app",
               "ui/ux", "ux"],
        "ar": ["موقع", "مواقع", "تصميم المواقع", "متجر إلكتروني", "متجر الكتروني", "متاجر", "صفحة هبوط",
               "استضافة", "دومين", "نطاق"],
    },
    "automation_ai": {
        "en": ["ai", "automation", "automate", "automated", "chatbot", "chat bot", "bot", "agent",
               "agents", "n8n", "zapier", "make.com", "whatsapp api", "workflow", "gpt", "chatgpt",
               "artificial intelligence", "machine learning"],
        "ar": ["ذكاء اصطناعي", "الذكاء الاصطناعي", "أتمتة", "اتمتة", "شات بوت", "روبوت", "بوت",
               "محادثة آلية", "وكيل ذكي"],
    },
    "offer": {  # a post that sells: price, discount, deadline or a call to act
        "en": ["omr", "ro", "price", "prices", "pricing", "discount", "offer", "off", "free", "limited",
               "book", "dm", "call us", "contact us", "whatsapp us", "link in bio", "order now", "package",
               "packages", "starting from"],
        "ar": ["ر.ع", "ريال", "سعر", "أسعار", "اسعار", "خصم", "عرض", "عروض", "مجان", "مجاناً", "احجز",
               "تواصل", "اطلب", "باقة", "باقات", "لفترة محدودة", "رابط في البايو"],
    },
}


def _compile_themes():
    out = {}
    for name, words in THEMES.items():
        en = r"\b(?:" + "|".join(re.escape(w) for w in words["en"]) + r")\b"
        ar = "|".join(re.escape(w) for w in words["ar"])
        out[name] = (re.compile(en, re.I), re.compile(ar))
    return out


THEME_RX = _compile_themes()


def tag_caption(caption):
    text = caption or ""
    return [name for name, (en, ar) in THEME_RX.items() if en.search(text) or ar.search(text)]


# --------------------------------------------------------------------------- tokens

def load_tokens():
    values = {}
    if TOKEN_FILE.exists():
        for line in TOKEN_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("IG_TOKEN", "FB_TOKEN"):
        if os.environ.get(k):
            values[k] = os.environ[k]
    return values.get("IG_TOKEN", ""), values.get("FB_TOKEN", "")


# --------------------------------------------------------------------------- http

class Graph:
    """Minimal Graph client. Every failure lands in self.errors, never raised."""

    def __init__(self, base, token, label):
        self.base, self.token, self.label = base, token, label
        self.errors = []
        self.calls = 0

    def _scrub(self, text):
        return str(text).replace(self.token, "<token>") if self.token else str(text)

    def get(self, path, **params):
        params["access_token"] = self.token
        url = f"{self.base}/{path.lstrip('/')}?{urllib.parse.urlencode(params)}"
        for attempt in range(3):
            self.calls += 1
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                try:
                    err = json.loads(body).get("error", {})
                except ValueError:
                    err = {"message": body[:300]}
                # 4 / 17 / 32 / 613 are Meta's rate-limit codes: wait, then retry.
                if err.get("code") in (4, 17, 32, 613) and attempt < 2:
                    time.sleep(60 * (attempt + 1))
                    continue
                shown = {k: v for k, v in params.items() if k != "access_token"}
                self.errors.append({"api": self.label, "path": path, "params": shown,
                                    "status": e.code, "code": err.get("code"),
                                    "subcode": err.get("error_subcode"),
                                    "message": self._scrub(err.get("message", ""))})
                return None
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < 2:
                    time.sleep(5)
                    continue
                self.errors.append({"api": self.label, "path": path, "message": self._scrub(e)})
                return None
        return None


# --------------------------------------------------------------------------- own account

def pull_account(g, days):
    me = g.get("me", fields="user_id,username,name,account_type,followers_count,follows_count,"
                            "media_count,biography,website")
    if not me:
        return None
    uid = me.get("user_id") or me.get("id")
    today = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    def window(n):
        return int((today - dt.timedelta(days=n)).timestamp()), int(today.timestamp())

    totals = {}
    for label, n in (("last_7_days", 7), ("last_28_days", 28)):
        since, until = window(n)
        totals[label] = {}
        for metric in ACCOUNT_TOTALS:
            r = g.get(f"{uid}/insights", metric=metric, period="day", metric_type="total_value",
                      since=since, until=until)
            if r and r.get("data"):
                totals[label][metric] = r["data"][0].get("total_value", {}).get("value")

    # Daily series: reach and follower_count support period=day time series, but
    # only across a 30-day span per call and follower_count only for 30 days back.
    series = {}
    since, until = window(min(days, 30))
    for metric in ("reach", "follower_count"):
        r = g.get(f"{uid}/insights", metric=metric, period="day", since=since, until=until)
        if r and r.get("data"):
            series[metric] = [{"date": v["end_time"][:10], "value": v["value"]}
                              for v in r["data"][0].get("values", [])]

    return {"profile": me, "totals": totals, "daily": series}, uid


def pull_demographics(g, uid):
    out = {}
    for metric in DEMOGRAPHIC_METRICS:
        out[metric] = {}
        for breakdown in DEMOGRAPHIC_BREAKDOWNS:
            r = g.get(f"{uid}/insights", metric=metric, period="lifetime", metric_type="total_value",
                      timeframe="this_month", breakdown=breakdown)
            if r and r.get("data"):
                rows = (r["data"][0].get("total_value", {}).get("breakdowns") or [{}])[0].get("results", [])
                out[metric][breakdown] = sorted(
                    ({"key": row["dimension_values"][0], "value": row["value"]} for row in rows),
                    key=lambda x: -x["value"])
    return out


def paged_media(g, path, limit):
    items, after = [], None
    while len(items) < limit:
        params = {"fields": MEDIA_FIELDS, "limit": min(50, limit - len(items))}
        if after:
            params["after"] = after
        r = g.get(path, **params)
        if not r:
            break
        items.extend(r.get("data", []))
        after = r.get("paging", {}).get("cursors", {}).get("after")
        if not after or "next" not in r.get("paging", {}):
            break
    return items[:limit]


def post_insights(g, media):
    kind = "REELS" if media.get("media_product_type") == "REELS" else "FEED"
    if media.get("media_product_type") == "STORY":
        return {}
    metrics = POST_METRICS[kind]
    r = g.get(f"{media['id']}/insights", metric=",".join(metrics))
    if r is None:
        # One unsupported metric sinks the batch; retry one by one and keep what works.
        g.errors.pop()
        got = {}
        for m in metrics:
            one = g.get(f"{media['id']}/insights", metric=m)
            if one and one.get("data"):
                got[m] = one["data"][0].get("values", [{}])[0].get("value")
        return got
    return {d["name"]: d.get("values", [{}])[0].get("value") for d in r.get("data", [])}


def pull_posts(g, uid, limit):
    posts = paged_media(g, f"{uid}/media", limit)
    rows = []
    for p in posts:
        ins = post_insights(g, p)
        rows.append({
            "date": p.get("timestamp", "")[:10],
            "type": p.get("media_product_type") or p.get("media_type"),
            "themes": ",".join(tag_caption(p.get("caption"))),
            "likes": p.get("like_count"),
            "comments": p.get("comments_count"),
            **{m: ins.get(m) for m in sorted({m for v in POST_METRICS.values() for m in v})},
            "permalink": p.get("permalink"),
            "caption": (p.get("caption") or "").replace("\n", " ")[:300],
        })
    return rows


# --------------------------------------------------------------------------- competitors

def read_competitors():
    out = []
    for line in COMPETITORS_FILE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        out.append({"handle": parts[0].lstrip("@"),
                    "segment": parts[1] if len(parts) > 1 else "",
                    "note": parts[2] if len(parts) > 2 else ""})
    return out


def fb_ig_user_id(fb):
    """Our IG account's id on the Facebook side (it differs from the Instagram-Login id)."""
    r = fb.get("me/accounts", fields="name,instagram_business_account{id,username}")
    for page in (r or {}).get("data", []):
        iba = page.get("instagram_business_account")
        if iba:
            return iba["id"], iba.get("username"), page.get("name")
    return None, None, None


def pull_competitor(fb, our_id, handle, posts):
    fields = (f"business_discovery.username({handle})"
              f"{{username,name,biography,website,followers_count,follows_count,media_count,"
              f"media.limit({posts}){{{MEDIA_FIELDS}}}}}")
    r = fb.get(our_id, fields=fields)
    return (r or {}).get("business_discovery")


def summarise_competitor(c, bd):
    media = (bd.get("media") or {}).get("data", [])
    followers = bd.get("followers_count") or 0
    dates = sorted(m["timestamp"] for m in media if m.get("timestamp"))
    span_days = 0
    if len(dates) > 1:
        first = dt.datetime.fromisoformat(dates[0].replace("+0000", "+00:00"))
        last = dt.datetime.fromisoformat(dates[-1].replace("+0000", "+00:00"))
        span_days = max((last - first).days, 1)
    likes = [m["like_count"] for m in media if m.get("like_count") is not None]
    comments = [m.get("comments_count") or 0 for m in media]
    tags = [tag_caption(m.get("caption")) for m in media]
    n = len(media) or 1

    def share(theme):
        return round(100 * sum(theme in t for t in tags) / n)

    avg_likes = round(sum(likes) / len(likes), 1) if likes else None
    avg_comments = round(sum(comments) / n, 1)
    return {
        "handle": c["handle"], "segment": c["segment"], "name": bd.get("name"),
        "followers": followers, "posts_total": bd.get("media_count"),
        "posts_sampled": len(media),
        "last_post": dates[-1][:10] if dates else "",
        "posts_per_week": round(len(media) / span_days * 7, 1) if span_days else "",
        "reels_pct": round(100 * sum(m.get("media_product_type") == "REELS" for m in media) / n),
        "avg_likes": avg_likes, "avg_comments": avg_comments,
        "engagement_pct": (round(100 * ((avg_likes or 0) + avg_comments) / followers, 2)
                           if followers and avg_likes is not None else ""),
        "likes_hidden": len(likes) < len(media),
        "website_pct": share("website"), "automation_ai_pct": share("automation_ai"),
        "offer_pct": share("offer"),
        "website": bd.get("website"),
        "ad_library": ("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                       "&country=ALL&search_type=keyword_unordered&q="
                       + urllib.parse.quote(bd.get("name") or c["handle"])),
    }


# --------------------------------------------------------------------------- output

def write_csv(path, rows):
    if not rows:
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel reads Arabic
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--posts", type=int, default=60, help="our posts to pull insights for")
    ap.add_argument("--competitor-posts", type=int, default=25, help="recent posts per competitor")
    ap.add_argument("--days", type=int, default=30, help="daily series length (max 30)")
    ap.add_argument("--no-competitors", action="store_true")
    ap.add_argument("--only-competitors", action="store_true")
    args = ap.parse_args()

    ig_token, fb_token = load_tokens()
    out = ROOT / ".tmp" / "ig" / dt.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    errors, calls = [], 0

    if not args.only_competitors:
        if not ig_token:
            sys.exit(f"No IG_TOKEN. Put IG_TOKEN=... in {TOKEN_FILE} (see tools/IG_PULL.md).")
        g = Graph(IG_GRAPH, ig_token, "instagram")
        got = pull_account(g, args.days)
        if not got:
            print(json.dumps(g.errors, indent=2))
            sys.exit("Could not read the account. The token is probably expired or lacks "
                     "instagram_business_basic.")
        account, uid = got
        prof = account["profile"]
        print(f"@{prof.get('username')}: {prof.get('followers_count')} followers, "
              f"{prof.get('media_count')} posts")
        (out / "account.json").write_text(json.dumps(account, indent=2, ensure_ascii=False))
        (out / "demographics.json").write_text(
            json.dumps(pull_demographics(g, uid), indent=2, ensure_ascii=False))
        rows = pull_posts(g, uid, args.posts)
        write_csv(out / "posts.csv", rows)
        print(f"  {len(rows)} posts with insights")
        errors += g.errors
        calls += g.calls

    if not args.no_competitors:
        if not fb_token:
            print("No FB_TOKEN: competitor step skipped (see tools/IG_PULL.md, step 3).")
        else:
            fb = Graph(FB_GRAPH, fb_token, "facebook")
            our_id, our_handle, page = fb_ig_user_id(fb)
            if not our_id:
                errors += fb.errors
                errors.append({"api": "facebook", "message": "No Facebook Page with a linked Instagram "
                               "business account is visible to FB_TOKEN. Link @ai.profit.lab.gcc to a "
                               "Page and grant pages_show_list + instagram_basic."})
                print(errors[-1]["message"])
            else:
                print(f"Business Discovery via @{our_handle} (Page: {page})")
                raw, summary, post_rows = {}, [], []
                for c in read_competitors():
                    bd = pull_competitor(fb, our_id, c["handle"], args.competitor_posts)
                    if not bd:
                        print(f"  @{c['handle']}: not available (personal/private account or renamed)")
                        continue
                    raw[c["handle"]] = bd
                    s = summarise_competitor(c, bd)
                    summary.append(s)
                    print(f"  @{c['handle']}: {s['followers']} followers, {s['posts_per_week']}/wk, "
                          f"web {s['website_pct']}% / ai {s['automation_ai_pct']}% / offer {s['offer_pct']}%")
                    for m in (bd.get("media") or {}).get("data", []):
                        post_rows.append({
                            "handle": c["handle"], "segment": c["segment"],
                            "date": m.get("timestamp", "")[:10],
                            "type": m.get("media_product_type") or m.get("media_type"),
                            "themes": ",".join(tag_caption(m.get("caption"))),
                            "likes": m.get("like_count"), "comments": m.get("comments_count"),
                            "permalink": m.get("permalink"),
                            "caption": (m.get("caption") or "").replace("\n", " ")[:400],
                        })
                (out / "competitors.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False))
                write_csv(out / "competitors_summary.csv", summary)
                write_csv(out / "competitors_posts.csv", post_rows)
                errors += fb.errors
            calls += fb.calls

    (out / "errors.json").write_text(json.dumps(errors, indent=2, ensure_ascii=False))
    print(f"\n{calls} API calls, {len(errors)} errors -> {out.relative_to(ROOT)}/")
    if errors:
        print("Some metrics failed (normal for a new or small account); see errors.json.")


if __name__ == "__main__":
    main()
