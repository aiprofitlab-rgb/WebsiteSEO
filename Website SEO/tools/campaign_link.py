#!/usr/bin/env python3
"""
Build tagged campaign links for the Smart Storefront launch.

    python3 tools/campaign_link.py --list
    python3 tools/campaign_link.py linkedin_dm --content batch1
    python3 tools/campaign_link.py whatsapp --content warm_list --ar
    python3 tools/campaign_link.py instagram_ad --content video_a --campaign winter_push

Why a tool and not a note in a file: the printed flyer went out with
`?utm_source=flyer` and no `utm_medium`. GA4 needs the MEDIUM to place a
session in a channel, so those scans land in "Unassigned" - attributed, but
in the bucket nobody reads. The site now patches that one case on arrival
(see the campaign normaliser in the storefront page head), but the real fix
is to never hand out an untagged link again, and a preset table is harder to
get wrong than remembering five parameters per message.

Every preset therefore carries a medium. There is no way to ask this script
for a link without one.

The three parameters, in the words that matter:
  utm_source   WHERE it was seen        linkedin, whatsapp, flyer, instagram
  utm_medium   WHAT KIND of placement   outreach, social, paid_social, print
  utm_campaign WHICH push               smart_storefront_launch
  utm_content  WHICH VARIANT            batch1, video_a, card_back
                                        - this is the one that answers
                                          "which message worked", so use it.
"""

import argparse
import sys
from urllib.parse import urlencode

EN = "https://aiprofitlab.io/en/smart-storefront/"
AR = "https://aiprofitlab.io/smart-storefront-ar/"

CAMPAIGN = "smart_storefront_launch"

# source, medium, and a one-line note on when to reach for it.
PRESETS = {
    "flyer": ("flyer", "print",
              "The printed butterfly flyer. Already baked into the QR of the "
              "current print run as source-only; the page fills in the medium."),
    "linkedin_dm": ("linkedin", "outreach",
                    "A direct message you sent by hand. Use --content to name the batch."),
    "linkedin_post": ("linkedin", "social",
                      "A public post or comment on your own feed."),
    "whatsapp": ("whatsapp", "outreach",
                 "A WhatsApp message you sent to one person or a broadcast list."),
    "instagram_bio": ("instagram", "social", "The link in the profile bio."),
    "instagram_story": ("instagram", "social", "A story sticker or swipe-up."),
    "instagram_ad": ("instagram", "paid_social", "A paid placement on Instagram."),
    "facebook_ad": ("facebook", "paid_social", "A paid placement on Facebook."),
    "google_ads": ("google", "cpc",
                   "Google Ads. Prefer auto-tagging (gclid) and leave UTMs off "
                   "entirely unless auto-tagging is switched off."),
    "email": ("email", "email", "A newsletter or a one-to-one email."),
    "qr_card": ("card", "print", "The 105x45mm hand-out card, if it is ever reprinted."),
}


def build(preset, content, campaign, arabic, base=None):
    source, medium, _ = PRESETS[preset]
    url = base or (AR if arabic else EN)
    params = [
        ("utm_source", source),
        ("utm_medium", medium),
        ("utm_campaign", campaign),
    ]
    if content:
        params.append(("utm_content", content))
    return url + "?" + urlencode(params)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("preset", nargs="?", help="one of the presets; --list to see them")
    ap.add_argument("--content", default="",
                    help="which variant: batch1, video_a, card_back. Strongly recommended "
                         "- it is what tells two messages apart in the report.")
    ap.add_argument("--campaign", default=CAMPAIGN, help=f"default: {CAMPAIGN}")
    ap.add_argument("--ar", action="store_true", help="point at the Arabic storefront page")
    ap.add_argument("--url", default="", help="override the landing page entirely")
    ap.add_argument("--list", action="store_true", help="show every preset and exit")
    args = ap.parse_args()

    if args.list or not args.preset:
        width = max(len(k) for k in PRESETS)
        print("preset".ljust(width), "source/medium".ljust(26), "when to use it")
        print("-" * (width + 28 + 40))
        for name, (src, med, note) in PRESETS.items():
            print(name.ljust(width), f"{src}/{med}".ljust(26), note)
        print("\nEvery preset carries a medium. That is the point of the table.")
        return 0 if args.list else 1

    if args.preset not in PRESETS:
        print(f"unknown preset {args.preset!r}. --list shows them all.", file=sys.stderr)
        return 1

    link = build(args.preset, args.content, args.campaign, args.ar, args.url or None)
    print(link)

    if not args.content:
        print("\nnote: no --content. The link works, but every message sent through this\n"
              "      channel will look identical in the report. Name the variant.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
