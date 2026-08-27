#!/usr/bin/env python3
"""One article, rendered through article_kit — the reference instance.

The text is a v4-voice rewrite of the published piece at
blog/en/2026-06-25-true-cost-missed-whatsapp-inquiries-oman.html. It keeps that
article's formula and worked examples and drops every unsourced percentage in
it ("78% expect a reply in 5 minutes", "over 90% of the population"), because
the v4 set does not publish a statistic it cannot point at. What is left is
arithmetic on the reader's own numbers, which is the stronger argument anyway
and the same stance the home page calculator takes.

To add the next article: copy this file, change ARTICLE, add the module name to
MODULES in build_v4.py. Nothing else moves.
"""
import article_kit as ak

CSS = ak.ARTICLE_CSS
JS = ak.ARTICLE_JS

ARTICLE = {
    "path": "/blog/en/2026-06-25-true-cost-missed-whatsapp-inquiries-oman/",
    "cat": "The cost of silence",
    "title": "What silence costs: putting a number on the messages you never answered",
    "dek": ("Twelve unread WhatsApp messages on a Sunday morning is not a customer service problem. "
            "It is a number. Here is the arithmetic that produces it &mdash; using your figures, not mine."),
    "date": "25 June 2026",
    "iso": "2026-06-25",
    "updated": "19 August 2026",
    "iso_updated": "2026-08-19",
    "image": "/blog/images/whatsapp_missed_inquiries_cost_oman.png",
    "alt": "Unanswered WhatsApp inquiries stacking up overnight for an Omani business",
    "caption": "Every unanswered message was a buyer who had already chosen you, right up until the silence.",

    "takeaways": [
        "A missed inquiry is not a service failure. It is a paid-for lead you already bought and then dropped.",
        "The formula needs four numbers and every one of them is yours: weekly inquiries, the share that arrive after hours, your win rate on the ones you do answer, and your average order.",
        "Multiply, and you get one monthly figure. Compare that figure to whatever the fix costs, once.",
        "The number is what is <em>at stake</em> in those messages &mdash; not a promise of recovery. Treat any vendor who tells you otherwise with suspicion.",
    ],

    "body": [
        ("open", "You open WhatsApp on a Sunday morning and there are twelve messages from Friday night. "
                 "One asking whether you carry a part. One asking for a price on forty cartons. One that is "
                 "just <em>Hello</em>, sent at 9:40pm, from a number you do not recognise. You reply to all "
                 "twelve. Two reply back. The other ten already bought somewhere else."),
        ("p", "Every owner I meet in Muscat knows this happens. Almost none of them can tell me what it costs. "
              "And a leak you cannot put a number on is a leak nobody ever fixes, because it never has to "
              "compete for budget against the things that do have numbers &mdash; the rent, the van, the salary. "
              "So let us produce the number."),

        ("h2", "A missed message is not a missed call"),
        ("p", "A missed call is a moment. A missed WhatsApp message is a decision that stays on the buyer's "
              "screen. They can see, hours later, that you did not reply. They can see the two grey ticks. And "
              "sitting directly above your unanswered message in their chat list is the competitor who did "
              "answer."),
        ("p", "That is the first thing to be precise about: you did not lose a conversation, you lost a lead you "
              "had already paid for. The Instagram spend that put your number in front of them, the sign on the "
              "warehouse, the years of being the name people pass on &mdash; all of that was spent to produce that "
              "message. The silence is where the money leaves, and it leaves after you have already paid to "
              "acquire it."),
        ("pull", "You are not losing customers. You are paying full price for leads and then dropping them "
                 "after midnight."),

        ("h2", "The four numbers you already have"),
        ("p", "You do not need analytics for this. You need four figures, and you can get all four from your own "
              "phone in about twenty minutes."),
        ("steps", [
            ("Inquiries in a normal week",
             "Scroll back seven days in WhatsApp and count the distinct people who asked you something. Not "
             "messages &mdash; people. A normal week, not your best one."),
            ("The share that landed outside working hours",
             "Of those, how many arrived after you closed, on a Friday, or during a prayer break? This is the "
             "portion where speed was never possible, only automation was."),
            ("Your win rate on the ones you did answer",
             "Of the inquiries you replied to promptly, how many turned into an order? For a workshop this "
             "might be one in four. For project quotes, one in ten. Use your own record and round down."),
            ("Your average order value",
             "Not your best invoice. The middle one. If you sell to both walk-ins and trade accounts, run the "
             "arithmetic twice rather than averaging two different businesses together."),
        ]),

        ("h2", "Run the arithmetic"),
        ("p", "With those four numbers the formula is one line, and it contains no assumption of mine:"),
        ("formula", "Monthly revenue at stake",
                    "weekly inquiries &times; <em>4.33</em> &times; after-hours share &times; win rate &times; average order"),
        ("p", "The 4.33 is just weeks in a month. Everything else came from your phone. Three worked examples, "
              "with the kind of figures owners in Oman actually give me &mdash; substitute your own:"),
        ("table",
         ["Business", "Inquiries / week", "After hours", "Win rate", "Avg order", "At stake / month"],
         [["Auto workshop, Ghala", "~30", "~35%", "~25%", "~OMR 90", "~OMR 1,023"],
          ["Building-materials trader, Rusayl", "~22", "~45%", "~15%", "~OMR 420", "~OMR 2,701"],
          ["Villa rentals, Al Khuwair", "~18", "~50%", "~10%", "~OMR 800", "~OMR 3,118"]],
         "Illustrations, not benchmarks. The formula is the point; the inputs must be yours."),
        ("callout", "", "What this number is and is not",
         "This is the revenue <em>at stake</em> in the messages you did not answer &mdash; not revenue you are "
         "guaranteed to recover. Some of those buyers were never going to order. Some will come back on Monday "
         "regardless. Recovering even a third of it changes the year.",
         "I am deliberately not multiplying it by a recovery rate, because I would be inventing that rate and "
         "you would have no way to check it. Anyone quoting you a fixed recovery percentage is doing exactly that."),

        ("h2", "The leak is wider than the formula"),
        ("p", "The four-term formula only counts the first order. Three costs sit outside it, and in a "
              "relationship market they are often larger than the sum you just calculated:"),
        ("ul", [
            "<strong>The advertising you already spent.</strong> If you spend on ads to make the phone ring, "
            "every unanswered message is that spend, delivered and then thrown away. Divide monthly ad spend by "
            "inquiries generated and you have the exact cost of each dropped one.",
            "<strong>The lifetime, not the invoice.</strong> A distributor who orders monthly is not worth one "
            "order. The formula prices the first transaction only, which is the most conservative reading "
            "available.",
            "<strong>What gets said about you.</strong> In a market this small, the buyer who was ignored on a "
            "Friday evening tells people. That cost never appears on any statement and never stops.",
        ]),

        ("cta", "Rather not do the arithmetic by hand?",
         "The simulator runs this exact formula on four sliders you set yourself, and shows the monthly figure "
         "against the one-time cost of closing the gap. Nothing is stored and nothing is sent.",
         "Open the simulator on WhatsApp",
         "Hello%20Nahid%2C%20I%20ran%20the%20numbers%20on%20missed%20inquiries%20and%20want%20to%20talk%20about%20them."),

        ("h2", "What actually closes the gap"),
        ("p", "Once you have a monthly figure, the decision stops being a matter of taste. It is one number "
              "against another. There are three honest ways to close an after-hours gap, and they are not "
              "equivalent:"),
        ("table",
         ["Approach", "What it costs", "What it fixes", "What it does not"],
         [["Another person on the phone", "~Monthly, forever",
           "Daytime volume when one person is not enough",
           "The 9pm message, Fridays, and two buyers at once"],
          ["WhatsApp auto-reply template", "~Free",
           "Tells the buyer you exist",
           "Answers nothing &mdash; a holding message is still silence with better manners"],
          ["A buyer agent that answers", "~OMR 950 once",
           "Answers in Arabic or English at any hour, then hands a live buyer to you on WhatsApp",
           "Judgement calls &mdash; those are routed to you deliberately, not guessed at"]],
         "The Smart Website price is the founding one-time figure published on the services page. Care is optional at OMR 75/month and cancellable."),
        ("p", "The comparison that matters is not between the three rows. It is between your monthly figure and "
              "the one-time one. If the arithmetic says OMR 1,023 a month is walking away, a one-time OMR 950 "
              "stops being an expense and becomes a payback period &mdash; in that case, twenty-eight days."),
        ("callout", "warn", "Before you automate anything, read this",
         "Anything that answers your buyers is now handling personal data under Oman's Personal Data Protection "
         "Law (Royal Decree 6/2022). That means a stated purpose, a way to consent, and somewhere defensible for "
         "the data to live. It is not onerous, but it is not optional, and it is the part most vendors skip in "
         "the demo."),

        ("h2", "Do the sum before you buy anything"),
        ("p", "I would rather you ran this formula and concluded that your leak is OMR 90 a month than bought "
              "anything from me. At OMR 90 a month, do not automate &mdash; answer faster and keep your money."),
        ("p", "But most owners who actually sit down and count are surprised by the size of it, because the "
              "messages arrive one at a time and the loss only exists in aggregate. Twelve unanswered messages "
              "is not twelve moments of poor service. It is one number, once a month, every month, until "
              "somebody puts it on a page."),
        ("quote", "Every success starts with insight. The number is the insight. What you do about it is a "
                  "separate decision &mdash; but you cannot make it without the number.",
                  "AI Profit Lab"),
    ],

    "faq": [
        ("How do I calculate what missed WhatsApp inquiries cost my business in Oman?",
         "Count the distinct people who message you in a normal week, multiply by 4.33 for a month, multiply by "
         "the share arriving outside working hours, then by the share of answered inquiries you normally win, "
         "then by your average order value in OMR. The result is the revenue at stake each month in messages "
         "you did not answer."),
        ("Is that figure the revenue I would recover with automation?",
         "No. It is what is at stake, not what is recoverable. Some of those buyers were never going to order "
         "and some return anyway. Treat any vendor who converts it into a guaranteed recovery figure with "
         "suspicion &mdash; that conversion rate is invented."),
        ("Why is after-hours the part that matters most?",
         "Because it is the only part a faster human cannot fix. Daytime volume can be answered by hiring. A "
         "message at 9:40pm on a Friday can only be answered by something that does not sleep, or by nobody."),
        ("Does a WhatsApp Business auto-reply solve this?",
         "It reduces the feeling of being ignored and nothing else. A buyer asking whether you carry a part "
         "needs the answer, not a promise of one. If the real reply still arrives on Monday, the buyer has "
         "already bought elsewhere."),
        ("What does it cost to close the gap?",
         "The Smart Website &mdash; a bilingual site with a buyer agent that answers in Arabic and English and "
         "hands live buyers to WhatsApp &mdash; is OMR 950 one-time at the founding price, with no required monthly "
         "fee. Optional care is OMR 75 a month and can be cancelled."),
        ("Does answering buyers automatically create a data protection problem in Oman?",
         "It creates a data protection responsibility. Under the Personal Data Protection Law (Royal Decree "
         "6/2022) you need a stated purpose for collecting the data, a consent mechanism, and secure handling. "
         "That is designed in from the start rather than added later."),
    ],

    "refs": [
        ("Oman Personal Data Protection Law &mdash; Royal Decree 6/2022 (MTCIT)",
         "https://www.mtcit.gov.om/"),
        ("WhatsApp Business Platform &mdash; official documentation",
         "https://business.whatsapp.com/"),
        ("AI Profit Lab &mdash; published prices for the Smart Website",
         "https://aiprofitlab.io/en/services/#price"),
    ],

    "related": [
        ("Silence", "The Silent Buyer Test: what a real buyer sees when they message you",
         "/en/contact/#test"),
        ("Arithmetic", "Run your own numbers in the revenue leak simulator",
         "/en/simulators/"),
        ("Demo", "Watch the buyer agent answer at 9:40pm, in Arabic",
         "/en/demos/"),
    ],
}


def body():
    return ak.render(ARTICLE)


META = dict(
    slug="article",
    title="What silence costs: pricing the WhatsApp messages you never answered | AI Profit Lab",
    desc=("The four-term formula for what missed WhatsApp inquiries cost an Omani business each month, "
          "worked through with real figures - and what it does not prove."),
    nav="/blog/",
    next=("Next", "Run your own numbers", "/en/simulators/"),
    schema=ak.schema(ARTICLE),
    # Aiden runs here like everywhere else (2026-08-27). Nothing in this skin
    # is pinned to the bottom corner any more, and the widget sends the article
    # text with each message, so a reader can ask about the piece in front of
    # them - see tools/reskin_articles.py, which owns the live articles.
    aiden=True,
)
