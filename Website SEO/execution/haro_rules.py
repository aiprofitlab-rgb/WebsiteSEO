#!/usr/bin/env python3
"""
The rules every HARO pitch is held to, in one place: who Nahid is (the only facts a pitch may
state), how to screen a journalist's request, how to draft the reply, how Claude reviews it,
and the checks a draft must pass.

Standard library only, and Python 3.9 syntax: the Antigravity agent's terminal sandbox runs a
copy of this file (next to haro.py, a copy of haro_agent.py) with whatever python3 it finds.

Used by:
  haro_email_processor.py  the Gemini API drafter (the fallback: Mac 22:00 and GitHub)
  haro_agent.py            Antigravity drafts, Claude reviews, code sends or leaves a draft
"""

import re

# ---------------------------------------------------------------------------
# Who the pitches speak for. A pitch may state only these facts about Nahid or AI Profit
# Lab; anything else he adds himself through an [ADD: ...] placeholder. Sourced on
# 2026-10-16 from the live About page and the aiprofitlab-brand skill. Never put a client
# name, result, percentage or year count here unless Nahid has confirmed it.
# ---------------------------------------------------------------------------
SPOKESPERSON_FACTS = """\
- Name: Nahid Abyari. Title: Founder, AI Profit Lab (https://aiprofitlab.io), based in Muscat, Oman.
  LinkedIn: https://www.linkedin.com/in/nahid-aby. Email: hello@aiprofitlab.io. There is no public
  headshot link yet.
- AI Profit Lab is not an agency. It is one engineer, Nahid, who does the work himself, in Arabic and English.
- He is an engineer who built and ran a real distribution business: importing, storage, catalogues,
  price tiers, quotes, shipping, invoices and the follow-up nobody has time for. (Never name the
  country that business is in.)
- What it taught him: the bottleneck was not price or product but response time. A buyer's message
  that arrived at 9pm and got answered at 8am had already bought somewhere else.
- So he built what he needed: a system that answers buyers in Arabic and English, knows the stock
  and the terms of sale, and passes him only the buyers worth his time. That became AI Profit Lab.
- AI Profit Lab builds done-for-you AI automation for small and mid-sized trading, distribution and
  service businesses in Oman and the GCC: WhatsApp and website assistants that answer buyers,
  missed-call follow-up, lead capture, quote and invoice automation, owner dashboards, and websites
  with search visibility (SEO). It audits the bottleneck, builds the system, runs it and trains the team.
- His working rules: plain language; prices published on the site; what is not included is stated
  up front; no invented numbers.
- Who he turns away: large companies and ERP projects, buyers who only want the cheapest option,
  businesses with no digital presence yet, and "make us go viral" requests.
- He does NOT have: a corporate CIO/CTO/CISO role, a nonprofit or government role, medical, legal,
  financial-advisory or academic credentials, US/UK/EU residence, or published client case studies."""

# The brand's banned hype words (aiprofitlab-brand skill).
BANNED_WORDS = ['synergy', 'leverage', 'transform', 'revolutionary', 'cutting-edge', 'disrupt',
                'seamless', 'enterprise-grade', 'growth-hack', '10x', 'game-changer', 'unlock']

WRITE_YOURSELF = "[WRITE IT YOURSELF] "

# ---------------------------------------------------------------------------
# Screening: PITCH or SKIP for every request. Shared by the Gemini API screener and the
# Antigravity brief, so both judge eligibility the same way.
# ---------------------------------------------------------------------------
SCREENING_RULES = """\
Decide PITCH only when all four hold:
1. ELIGIBLE: he is the kind of person the journalist asks for. Read who should respond and every
   requirement: role, seniority, company size, industry, credential, country or city, and personal
   experience ("CIOs at 250-2,000-employee firms", "nonprofit CTO", "US-based", "licensed", "MD",
   "parents who", "homeowners", "women founders", "e-commerce store owners"). If any requirement
   rules him out, eligible=false and SKIP. Founders, small-business owners and AI or automation
   consultants or experts do fit when the request is open to them. A form field asking for your
   city, state or country so they can credit you is NOT a location requirement: skip on location
   only when the request says sources must be based somewhere.
2. TOPIC: something he can speak to from experience: practical AI adoption in small and mid-sized
   businesses; AI agents, chatbots and assistants for customer messages and sales; WhatsApp and
   customer-service automation; automating admin work (quotes, invoices, follow-up, data entry);
   running a small trading, distribution or service business; websites, SEO and AI search for small
   businesses; choosing AI tools and models on a small budget; founder life in an AI-first one-person
   company; business and technology in Oman, the GCC and the Middle East.
3. NOT pay-to-play: no sponsored placements, paid awards or listings, product samples, gift guides or
   products to review.
4. SUBSTANCE: he can give a useful, honest answer without making up statistics or client stories.
   A request that needs real numbers or examples from his own business is fine: the draft will leave
   placeholders for him.

Requests often mention products, launches or news newer than anything you know about. Take the
journalist's description as true; never skip a request because you don't recognise something in it.

fit: 1-5, how strong a source he is for this request (5 = exactly who they want). A PITCH needs fit 3+.
Generic business-advice requests (networking, productivity, leadership, hiring or general
"expert tips" roundups) are fit 2 unless the request is about one of the topics in rule 2.
In each reason, describe him only by the facts above: never credit him with experience they don't state.
ai_replies_forbidden: true when the request says it rejects AI-written replies ("No AI pitches",
"written in your own words", "no AI-generated responses")."""

# ---------------------------------------------------------------------------
# Drafting: one reply per chosen request, or talking points when AI replies are rejected.
# ---------------------------------------------------------------------------
PITCH_TASK = """Write Nahid's reply, ready for him to review and send:
- Open with one sentence: who he is and why he can answer THIS request.
- Then answer the journalist's actual questions directly, in the order asked, in 2-4 short paragraphs
  or "- " bullets they can quote as-is. If they list things to include, include each one.
- Give a concrete opinion, a practical tip or how something works in practice, not generalities.
- 120-250 words unless the journalist asks for a different length."""

NOTES_TASK = """This journalist rejects AI-written replies, so do NOT write the reply. Write talking points
Nahid will turn into his own reply: 3-5 bullet points ("- "), one idea each, as short notes he can
expand (fragments are fine). After them add "They asked for:" and list what the journalist wants
included."""

DRAFT_RULES = """\
RULES
- First person, as Nahid. Plain, specific and calm: an operator talking, not a vendor selling.
- Never state that Nahid did, built, switched, chose, measured, tried, saw or experienced anything
  unless the facts above say so. Inventing his first-hand experience is the worst mistake a draft
  can make: a journalist will print it as true. The same goes for clients, case results,
  percentages, counts, years of experience, team size and awards. Never invent statistics about the
  world either.
- Opinions, explanations of how things work, and advice are fine: they don't claim experience.
- When the request asks for first-hand experience the facts don't cover, write those parts as
  placeholders for Nahid, e.g. [ADD: which model you replaced, with which, and why]. Inside a
  placeholder, say what to add; never suggest a number or an example answer. At most 3 placeholders.
- Do not name the country of his distribution business. Do not claim local roots or a network.
- Plain text only: no markdown, no headings, no bold. No greeting and no sign-off: both are added.
- Never use: synergy, leverage, transform, revolutionary, cutting-edge, disrupt, seamless,
  enterprise-grade, growth-hack, 10x, game-changer, unlock.

fit_note: one sentence for Nahid on why this request suits him and anything to watch.
only_if_true: the first-hand experience this reply depends on that the facts don't confirm, written
as a condition Nahid can check (e.g. "you have moved a live workflow from a large model to a smaller
one"). Empty when the reply relies only on the facts and on opinion."""

# ---------------------------------------------------------------------------
# Claude's review: fact-check, humanize, verdict. The writing-pattern list is condensed from
# the humanizer skill (Wikipedia's "Signs of AI writing"), cut to what shows up in a pitch.
# Its "add soul" advice is deliberately narrowed: an anecdote or a feeling about a past event
# would be invented experience here.
# ---------------------------------------------------------------------------
REVIEW_SYSTEM = """You are the final editor of pitches that Nahid Abyari, founder of AI Profit Lab, sends to
journalists who asked for expert sources. Another model drafted the pitch. Catch anything untrue
or off, and make it read like Nahid wrote it himself. You edit; you never add."""

REVIEW_TASK = """DO THREE THINGS

1. CHECK the draft. Note each problem in one sentence:
   - a statement about Nahid, AI Profit Lab, its clients or its results that the facts don't
     support, above all first-hand experience ("I built", "we switched", "our clients saw",
     "I've seen") the facts don't state;
   - a statistic, percentage, count, study, quote or named source the request didn't supply;
   - the country of his distribution business, or a claim of local roots or a network;
   - a requirement in the request he doesn't meet (role, seniority, company size, location,
     credential, personal experience): then eligible=false;
   - a question in the request the draft doesn't answer, or something the journalist asked to
     include that is missing: then answers_request=false;
   - anything a journalist would mind: selling, hype, filler, overclaiming, a pitch about the
     company instead of an answer.

2. REWRITE it so it reads like Nahid wrote it himself.
   - Fix each problem from step 1 by cutting or narrowing the sentence. Never fix by inventing.
   - Cut the marks of AI writing: inflated significance ("plays a pivotal role", "a testament to",
     "in today's landscape", "marks a shift"); AI vocabulary (additionally, crucial, delve,
     enhance, foster, garner, highlight as a verb, intricate, key as an adjective, landscape,
     navigate, pivotal, realm, robust, showcase, streamline, testament, underscore, vibrant,
     journey); "serves as" or "stands as" where "is" will do; "It's not just X, it's Y" and "not
     only... but also"; ideas forced into threes; synonym cycling; "-ing" tails that add fake
     depth (", ensuring...", ", highlighting..."); em dashes (use commas, full stops or
     brackets); curly quotes, emojis and bold; vague authorities ("experts say", "studies
     show"); stacked hedges ("could potentially"); filler ("in order to", "it's important to
     note that"); chatbot tics ("Great question", "I hope this helps", "Feel free to"); a
     generic upbeat ending; every sentence the same length and shape.
   - Sound like a person: vary sentence length, use plain words, give his opinion straight, in
     the first person. Calm and professional, quotable as-is. No slang, no jokes, no fake
     hesitation, no hype (never: synergy, leverage, transform, revolutionary, cutting-edge,
     disrupt, seamless, enterprise-grade, growth-hack, 10x, game-changer, unlock).
   - Hard limits: add no fact, number, example, anecdote, name, client, result or experience,
     however plausible. If the draft lacks something useful, leave it out. Keep every
     [ADD: ...] placeholder exactly as written. Keep his meaning, and keep the answers in the
     journalist's order. Plain text, no markdown, no greeting and no sign-off (both are added).
     120-250 words unless the request asks for another length.

3. DECIDE. verdict "send" only when, after your rewrite, none of the step-1 problems is left, he
   is eligible, it answers the request, and no [ADD: ...] placeholder remains. Otherwise "hold",
   with hold_reason saying in one sentence what Nahid must do.

fixed: the step-1 problems your rewrite removed. remaining: the ones still in your rewrite, each a
sentence Nahid can act on (a placeholder to fill counts). changes: one sentence on what you changed
in the voice. text: your rewrite, the whole reply."""

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "eligible": {"type": "boolean"},
        "answers_request": {"type": "boolean"},
        "fixed": {"type": "array", "items": {"type": "string"}},
        "remaining": {"type": "array", "items": {"type": "string"}},
        "changes": {"type": "string"},
        "text": {"type": "string"},
        "verdict": {"type": "string", "enum": ["send", "hold"]},
        "hold_reason": {"type": "string"},
    },
    "required": ["eligible", "answers_request", "fixed", "remaining", "changes", "text", "verdict",
                 "hold_reason"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
PLACEHOLDER = re.compile(r'\[ADD:[^\]]*\]')
_GREETING = re.compile(r'^\s*(hi|hello|hey|dear|greetings|good (morning|afternoon|evening))\b', re.I)
_SIGNOFF = re.compile(r'^\s*(best|regards|kind regards|warm regards|thanks|thank you|many thanks|cheers|'
                      r'sincerely|all the best|nahid)\b[^.!?]{0,40}$', re.I)
_MARKDOWN = re.compile(r'\*\*|__|^\s*#|`', re.M)
# The distribution business's country is never named (founder-background memory).
_COUNTRY = re.compile(r'\biran(ian)?\b', re.I)
_FIGURE = re.compile(r'\d[\d,.]*\d|\d')


def claims_to_check(text, query_text):
    """Numbers and banned words in a draft that the journalist's request doesn't explain."""
    context = query_text.lower()
    flags = []
    for m in re.finditer(r'\b\d[\d,.]*\s*(%|percent|per cent|x\b|clients?|customers?|businesses|companies|'
                         r'brands|years?|months?|staff|employees|people|projects)', text, re.I):
        if m.group(0).lower() not in context:
            flags.append(f'"{m.group(0)}"')
    for word in BANNED_WORDS:
        if re.search(rf'\b{re.escape(word)}', text, re.I) and word not in context:
            flags.append(f'banned word "{word}"')
    return flags


def figures(text):
    """Every number in a text, as written ("2,000", "24", "3.5")."""
    return set(_FIGURE.findall(text or ''))


def text_problems(text, query_text, notes_only):
    """What is wrong with a reply (or with talking points) as text, each as an instruction."""
    t = (text or '').strip()
    if not t:
        return ["the text is empty"]
    problems = []
    lines = [ln for ln in t.splitlines() if ln.strip()]
    if notes_only:
        head = t.split('They asked for:')[0]
        bullets = [ln for ln in head.splitlines() if ln.lstrip().startswith('- ')]
        if 'They asked for:' not in t:
            problems.append('talking points end with "They asked for:" and a list of what the journalist wants')
        if not 3 <= len(bullets) <= 6:
            problems.append(f'{len(bullets)} talking points before "They asked for:": write 3-5, each starting "- "')
    else:
        words = len(re.findall(r"[\w'’-]+", PLACEHOLDER.sub('', t)))
        if not 40 <= words <= 330:
            problems.append(f"{words} words: aim for 120-250 (40-330 even when the journalist asks for another length)")
        if _GREETING.match(lines[0]):
            problems.append("it starts with a greeting: \"Hi <name>,\" is added by code, so remove yours")
        if _SIGNOFF.match(lines[-1]):
            problems.append("it ends with a sign-off: the signature is added by code, so remove yours")
        placeholders = PLACEHOLDER.findall(t)
        if len(placeholders) > 3:
            problems.append(f"{len(placeholders)} [ADD: ...] placeholders: at most 3")
        for p in placeholders:
            if re.search(r'\d|e\.g\.|for example|such as', p, re.I):
                problems.append(f"the placeholder {p} suggests an answer: say only what Nahid should add")
    if _MARKDOWN.search(t):
        problems.append("it has markdown (**, __, # or `): plain text only")
    if _COUNTRY.search(t):
        problems.append("it names the country of Nahid's distribution business: never name it")
    for flag in claims_to_check(PLACEHOLDER.sub('', t), query_text):
        if flag.startswith('banned word'):
            problems.append(f"{flag}: use a plain word instead")
        else:
            problems.append(f"the figure {flag} is not in the request or the facts: remove it, or make it an "
                            f"[ADD: ...] placeholder")
    return problems
