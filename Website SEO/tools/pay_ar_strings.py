# -*- coding: utf-8 -*-
"""
Every user-visible string on the Arabic seat-claim page, and where its Arabic
came from.

WHY THIS FILE EXISTS AT ALL
---------------------------
A native reader reviewed the Arabic site and edited words away from what was
generated. That makes the Arabic already shipped in public_html/*-ar.html the
AUTHORITY, not a draft. Translating pay.html afresh would silently revert those
corrections, and nothing in the build would catch it, because both versions are
"valid Arabic".

So every string below records its provenance in `src`:

    HARVEST_*   lifted from reviewed Arabic that is already live. Do not
                "improve" these - a nicer synonym here is a regression.
    NEW         written by Claude, NEVER seen by the reviewer. This is the
                only category that needs a human pass, and `review_list()`
                prints exactly these with their English beside them.

Keeping the two apart is the whole point. Mixed together, the reviewer has to
re-read a whole page to find the forty sentences that are actually new.

DIGITS. Real figures use Western digits (97, 300, 50%), matching checkout-ar,
where Arabic-Indic numerals appear only as decorative step numerals (٠١، ٠٢).
Note smart-storefront-ar.html contains BOTH "عربون 50%" and "عربون ٥٠٪" - an
inconsistency inside reviewed copy. It is flagged, not silently resolved; see
OPEN_QUESTIONS at the bottom.

REGISTER. First person singular, per the standing voice rule - "أبني" not
"نبني". The corporate plural would contradict the claim the whole site makes.
"""

# --- provenance tags -------------------------------------------------------
H_CHECKOUT = "HARVEST_checkout-ar.html"
H_STOREFRONT = "HARVEST_smart-storefront-ar.html"
H_WORDS = "HARVEST_page_checkout.WORDS[ar]"
NEW = "NEW"


# ---------------------------------------------------------------------------
# 1. The seat-claim page's own HTML
# ---------------------------------------------------------------------------
HTML = [
    # key                     english                                          arabic                                                     src
    # The brand stays Latin in the title, as it does everywhere: it is the
    # registered name and the wordmark is Latin. See ar_common.py.
    ("page_title",            "Your seat — AI Profit Lab",                      "مقعدك — AI Profit Lab",                                   NEW),
    ("claim_title",           "Your claim",                                     "حجزك",                                                    NEW),
    ("looking_up",            "Looking up your seat…",                          "جارٍ البحث عن مقعدك…",                                    NEW),
    ("one_moment",            "One moment.",                                    "لحظة واحدة.",                                             NEW),
    ("business",              "Business",                                       "النشاط",                                                  H_WORDS),
    ("price_held",            "Price held for you",                             "السعر المحجوز لك",                                        NEW),
    ("deposit_label",         "Deposit to lock the seat (50%)",                 "عربون 50% لحجز المقعد",                                   H_STOREFRONT),
    ("pledged_back",          "Pledged back to you, after delivery",            "يُرَدّ إليك مقابل تعهّداتك، بعد التسليم",                  NEW),
    ("seat_confirmed_h",      "Your seat is confirmed.",                        "تم تأكيد مقعدك.",                                         NEW),
    ("invoice_is_receipt",    "Your invoice is in your inbox — that one is the receipt, so it's the one to keep.",
                              "فاتورتك في بريدك — وهي الإيصال، فهي التي تحتفظ بها.",                                                        NEW),

    # The card-safety sentence is reviewed copy and says more than the English
    # does. Kept verbatim rather than back-translated to match the English.
    ("card_safety",           "Card payment, on Thawani's own secure page. We never see or store your card number.",
                              "بيانات بطاقتك تُدخَل على صفحة مزوّد الدفع نفسه. ولا تُكتب في هذا الموقع ولا تُرسَل إليه ولا تُخزَّن فيه إطلاقاً.",
                                                                                                                                           H_CHECKOUT),
    ("pay_deposit_btn",       "Pay the deposit",                                "ادفع العربون",                                            H_WORDS),
    ("confirming_bank",       "Confirming your payment with the bank. This takes a few seconds — don't close the page.",
                              "جارٍ تأكيد دفعتك مع البنك. يستغرق هذا ثوانٍ قليلة — لا تغلق الصفحة.",                                          NEW),
    ("thawani_licence",       "Payments processed by Thawani · Licensed by the Central Bank of Oman",
                              "المدفوعات تُعالَج عبر Thawani · مرخّصة من البنك المركزي العُماني",                                             NEW),

    # --- bank transfer route ---
    ("transfer_q",            "Rather pay by bank transfer?",                   "تفضّل الدفع بتحويل بنكي؟",                                 NEW),
    ("transfer_body",         "Reply to the email your invoice came with, or message me below, and I'll send you the transfer details directly. I don't publish bank details on a page — that's how people get impersonated.",
                              "ردّ على البريد الذي وصلتك به الفاتورة، أو راسلني بالأسفل، وأرسل لك تفاصيل التحويل مباشرة. أنا لا أنشر بيانات بنكية على صفحة — فهكذا تحديداً يُنتحل اسم الناس.",
                                                                                                                                           NEW),
    ("upload_q",              "Already transferred it? Upload the receipt.",    "حوّلته بالفعل؟ ارفع الإيصال.",                              NEW),
    ("upload_body",           "A photo or PDF of the transfer confirmation. Up to 5 MB. It's stored privately and only I can open it.",
                              "صورة أو ملف PDF لتأكيد التحويل. حتى 5 ميغابايت. يُحفَظ بشكل خاص ولا يفتحه أحد غيري.",                          NEW),
    ("choose_receipt",        "Choose the receipt",                             "اختر الإيصال",                                            NEW),

    # --- the four steps ---
    ("step1_h",               "You claimed a seat",                             "حجزت مقعداً",                                             H_STOREFRONT),
    ("step1_b",               "Done — your details are with me.",               "تم — بياناتك وصلتني.",                                    NEW),
    ("step2_h",               "Your invoice is in your inbox",                  "فاتورتك في بريدك",                                        NEW),
    ("step2_b",               "Sent the moment you claimed, with everything you need to pay.",
                              "أُرسلت لحظة حجزك، وفيها كل ما تحتاجه للدفع.",                                                                NEW),
    ("step3_h",               "You pay the 50% deposit",                        "تدفع عربون 50%",                                          H_STOREFRONT),
    ("step3_b",               "By card here, or by transfer if you'd rather.",  "بالبطاقة هنا، أو بتحويل إن كنت تفضّل.",                     NEW),
    ("step4_h",               "Your seat is confirmed",                         "يتأكّد مقعدك",                                            NEW),
    ("step4_b",               "A card payment confirms itself instantly. A transfer confirms once I've seen it land.",
                              "الدفع بالبطاقة يتأكّد فوراً. والتحويل يتأكّد حين أراه وقد وصل.",                                               NEW),

    ("ask_anything",          "Ask me anything about this",                     "اسألني عن أي شيء في هذا",                                 NEW),

    # --- bad-reference state ---
    ("noref_h",               "I can't find that reference.",                   "لا أجد هذا الرقم المرجعي.",                                NEW),
    ("noref_b",               "Either the link got cut in half somewhere between the email and here, or the reference has a typo in it. Both are easily fixed.",
                              "إمّا أن الرابط انقطع في منتصفه بين البريد وهنا، أو أن في الرقم المرجعي خطأ مطبعي. وكلاهما يُصلَح بسهولة.",      NEW),
    ("noref_wa",              "Send me the reference on WhatsApp",              "أرسل لي الرقم المرجعي على واتساب",                         NEW),

    # --- chrome ---
    ("back_to_offer",         "Back to the offer",                              "العودة إلى العرض",                                        NEW),
    ("terms",                 "Terms",                                          "شروط الخدمة",                                             H_CHECKOUT),
    ("refund",                "Refund policy",                                  "سياسة الاسترداد",                                         H_CHECKOUT),
    ("privacy",               "Privacy",                                        "الخصوصية",                                                H_CHECKOUT),
    ("footer",                "AI Profit Lab — a brand of Lotus Gulf International (CR 1570092) · South Al Khuwair, Bousher, Muscat",
                              "AI Profit Lab — علامة تجارية تابعة لشركة Lotus Gulf International (س.ت 1570092) · الخوير الجنوبية، بوشر، مسقط",
                                                                                                                                           H_CHECKOUT),
]


# ---------------------------------------------------------------------------
# 2. Strings inside the page's own JavaScript
# ---------------------------------------------------------------------------
JS = [
    # --- status pills / labels ---
    ("pill_awaiting",         "Awaiting deposit",                               "بانتظار العربون",                                         NEW),
    ("pill_paid",             "Deposit paid (50%)",                             "العربون مدفوع (50%)",                                     NEW),
    ("pill_started",          "Payment started",                                "بدأ الدفع",                                               NEW),
    ("pill_receipt",          "Receipt received",                               "وصل الإيصال",                                             NEW),
    ("pill_confirmed",        "Seat confirmed",                                 "تأكّد المقعد",                                            NEW),
    ("deposit_row",           "Deposit to lock the seat (50%)",                 "عربون 50% لحجز المقعد",                                   H_STOREFRONT),

    # --- headline states ---
    ("held_h",                "Your seat is held.",                             "مقعدك محجوز.",                                            NEW),
    ("held_b",                "One payment away from confirmed. Your invoice is already in your inbox.",
                              "دفعة واحدة ويُصبح مؤكّداً. وفاتورتك في بريدك بالفعل.",                                                        NEW),
    ("done_h",                "That's your seat. Confirmed.",                   "هذا مقعدك. مؤكّد.",                                       NEW),
    ("done_b",                "Your deposit has cleared and the seat is yours at the price above.",
                              "عربونك وصل، والمقعد لك بالسعر أعلاه.",                                                                       NEW),
    ("transfer_b",            "Your invoice is in your inbox. This page is where you upload the transfer receipt.",
                              "فاتورتك في بريدك. وهذه الصفحة هي المكان الذي ترفع فيه إيصال التحويل.",                                        NEW),

    # --- progress ---
    ("opening",               "Opening the secure page…",                       "جارٍ فتح صفحة الدفع الآمن…",                              H_WORDS),
    # NOT a progress message, despite the English -ing. It is the heading of
    # the pay box on the transfer route, where the card button does not exist:
    # "this is how the deposit gets paid". An earlier draft read "جارٍ دفع
    # العربون" - "the deposit is being paid" - which tells a buyer who has not
    # paid anything that a payment is under way.
    ("pay_title_transfer",    "Paying the deposit",                             "دفع العربون",                                             NEW),

    # --- errors. Tone matters most here: never blame the buyer, always
    #     say plainly whether money moved. ---
    ("err_noref",             "No reference in this link.",                     "لا يوجد رقم مرجعي في هذا الرابط.",                        NEW),
    ("err_noseat",            "I can't find that seat.",                        "لا أجد هذا المقعد.",                                      NEW),
    ("err_gone",              "I can't find this claim any more. Message me with your reference and I'll find it.",
                              "لم أعد أجد هذا الحجز. راسلني برقمك المرجعي وسأجده لك.",                                                      NEW),
    ("err_ledger",            "I can't reach the ledger right now.",            "لا أستطيع الوصول إلى السجل الآن.",                        NEW),
    ("err_noamount",          "There's no amount on this claim yet. Message me and I'll fix it in a minute.",
                              "لا يوجد مبلغ على هذا الحجز بعد. راسلني وأصلحه خلال دقيقة.",                                                   NEW),
    ("err_closed",            "This claim has been closed. Message me and I'll tell you where things stand.",
                              "هذا الحجز أُغلق. راسلني وأخبرك أين وصلت الأمور.",                                                             NEW),
    ("err_card_off",          "Card payment isn't available at the moment. Open “Rather pay by bank transfer?” below and I'll send you the details straight away.",
                              "الدفع بالبطاقة غير متاح حالياً. افتح «تفضّل الدفع بتحويل بنكي؟» بالأسفل وأرسل لك التفاصيل فوراً.",              NEW),
    ("err_session",           "I couldn't open the secure payment page just now, and nothing has been charged. Try again, or use the bank transfer option below.",
                              "تعذّر عليّ فتح صفحة الدفع الآمن الآن، ولم يُحتسب شيء. حاول مرة أخرى، أو استخدم خيار التحويل البنكي بالأسفل.",   NEW),
    ("err_retry",             "Try the card payment again",                     "أعد المحاولة بالبطاقة",                                   NEW),
    ("err_filetype",          "That file type won't open for me. A JPG, PNG or PDF works.",
                              "هذا النوع من الملفات لا يفتح عندي. صيغة JPG أو PNG أو PDF تعمل.",                                             NEW),
    ("err_upload",            "The upload didn't go through. Send it to me on WhatsApp instead and I'll attach it myself.",
                              "لم يكتمل الرفع. أرسله لي على واتساب بدلاً من ذلك وأرفقه بنفسي.",                                              NEW),
    ("err_toobig",            "That file is over 5 MB. A photo of the screen is usually plenty — no need for the full-resolution one.",
                              "هذا الملف أكبر من 5 ميغابايت. صورة للشاشة تكفي عادةً — لا داعي للدقة الكاملة.",                                NEW),
    ("err_upload_offline",    "The upload couldn't reach the server. Send the receipt on WhatsApp and I'll take it from there.",
                              "لم يصل الرفع إلى الخادم. أرسل الإيصال على واتساب وأتولّى الأمر من هناك.",                                       NEW),

    # --- sublines. Each one is the quiet second sentence under a headline
    #     that has just delivered bad news, so each has to end somewhere the
    #     buyer can still act. ---
    ("noref_sub",             "Check the link in your email, or message me and I'll find you.",
                              "تحقّق من الرابط في بريدك، أو راسلني وسأجدك.",                                                                 NEW),
    ("noseat_sub",            "The reference didn't match anything in the ledger.",
                              "الرقم المرجعي لم يطابق شيئاً في السجل.",                                                                      NEW),
    ("ledger_sub",            "Your claim is safe — this page just can't read it at the moment.",
                              "حجزك بأمان — هذه الصفحة وحدها هي التي لا تستطيع قراءته الآن.",                                                NEW),
    ("done_sub",              "I'll be in touch about the brief. Nothing else is needed from you today.",
                              "سأتواصل معك بخصوص الموجز. لا شيء آخر مطلوب منك اليوم.",                                                       NEW),

    # --- eyebrow and pill states the script swaps in ---
    ("eyebrow_thatsdone",     "That's done",                                    "تمّ ذلك",                                                 NEW),
    ("eyebrow_paid",          "Paid",                                           "مدفوع",                                                   NEW),
    ("head_seat",             "Your seat.",                                     "مقعدك.",                                                  NEW),
    ("pill_closed",           "Closed",                                         "مُغلق",                                                   NEW),

    # --- the transfer route. render() rewrites four strings when the card
    #     gateway is off, and on that branch the transfer IS the offer, not a
    #     fallback. Steps 3 and 4 are rewritten to describe it. ---
    ("s3_transfer",           "By bank transfer. Reply to your invoice email and the details come straight back.",
                              "بتحويل بنكي. ردّ على بريد فاتورتك وتصلك التفاصيل فوراً.",                                                      NEW),
    ("s4_transfer",           "The moment I've seen the transfer land.",        "لحظة أن أرى التحويل وقد وصل.",                             NEW),
    ("paynote_transfer",      "Reply to the email your invoice came with and I'll send you the transfer details straight away. I don't publish bank details on a page — that's how people get impersonated.",
                              "ردّ على البريد الذي وصلتك به الفاتورة وأرسل لك تفاصيل التحويل فوراً. أنا لا أنشر بيانات بنكية على صفحة — فهكذا تحديداً يُنتحل اسم الناس.",
                                                                                                                                           NEW),
    ("receipt_on_file",       "A receipt is already on file. I'm checking the transfer — you don't need to do anything else. Upload again only if you sent the wrong file.",
                              "هناك إيصال محفوظ بالفعل. أنا أتحقّق من التحويل، ولا يلزمك شيء آخر. لا ترفع مرة أخرى إلا إن كنت قد أرسلت الملف الخطأ.",
                                                                                                                                           NEW),

    # --- the card button, and the round trip through the gateway ---
    ("pay_by_card",           "Pay {amount} by card",                           "ادفع {amount} بالبطاقة",                                  NEW),
    ("invoice_no",            "Invoice {no}",                                   "فاتورة {no}",                                             NEW),
    ("came_back",             "You came back without paying, and nothing was charged. Your seat is still held at this price — pay whenever you're ready.",
                              "عدت دون أن تدفع، ولم يُحتسب عليك شيء. مقعدك ما زال محجوزاً بهذا السعر — ادفع متى كنت مستعداً.",                 NEW),
    # Deliberately does not say the payment failed - we do not know that. It
    # says only what is true from here, and it says DON'T PAY AGAIN first.
    ("unconfirmed",           "Your payment hasn't shown up on my side yet. If your bank has confirmed it, don't pay again — ",
                              "دفعتك لم تظهر عندي بعد. إن كان بنكك قد أكّدها فلا تدفع مرة أخرى — ",                                           NEW),
    ("unconfirmed_link",      "message me",                                     "راسلني",                                                  NEW),
    ("unconfirmed_tail",      " and I'll sort it in minutes.",                  " وسأحلّها خلال دقائق.",                                    NEW),

    # --- the receipt upload button, through its four states ---
    ("uploading",             "Uploading…",                                     "جارٍ الرفع…",                                             NEW),
    ("try_another_file",      "Try another file",                               "جرّب ملفاً آخر",                                          NEW),
    ("upload_another",        "Upload another",                                 "ارفع ملفاً آخر",                                          NEW),
    ("try_again",             "Try again",                                      "أعد المحاولة",                                            NEW),
    ("upload_ok",             "Got it. I'll check the transfer has landed and confirm your seat — you'll get an email when I do. Nothing else needed from you.",
                              "وصلني. سأتأكّد من وصول التحويل ثم أؤكّد مقعدك، وسيصلك بريد حين أفعل. لا شيء آخر مطلوب منك.",                     NEW),

    # --- WhatsApp prefills. These are messages the BUYER sends me, so they
    #     are written in their voice, not mine. ---
    ("wa_about_seat",         "Hello — about my Smart Website seat, reference {ref}.",
                              "مرحباً — بخصوص مقعدي في الموقع الذكي، الرقم المرجعي {ref}.",                                                  NEW),
    ("wa_paid_unconfirmed",   "Hello — I paid for seat {ref} but the page hasn't confirmed it.",
                              "مرحباً — دفعت مقابل المقعد {ref} لكن الصفحة لم تؤكّد ذلك.",                                                    NEW),
    ("wa_upsell_booked",      "Hello Nahid - seat {ref}. I added the {name} at OMR {price}/month on the payment page. Please confirm it.",
                              "مرحباً ناهد — المقعد {ref}. أضفت {name} بـ {price} ر.ع. شهرياً في صفحة الدفع. أرجو تأكيده.",                    NEW),
]


# ---------------------------------------------------------------------------
# 3. The Visibility Desk offer, where it touches THIS page
#
# The interstitial itself is not here: its Arabic lives in
# page_checkout.UPSELL["ar"] and is already on the Arabic checkout, reviewed
# and live. What is here is the two blocks that exist ONLY on the seat page -
# the standing band the transfer route needs (there is no pay button to hang
# the offer on) and the confirmation block that shows once it is booked.
#
# No guarantee wording appears below, on purpose. A guarantee is a promise and
# it lives in exactly one place, the dialog. Both figures are substituted from
# pay.py at build time rather than typed, so the band cannot quote a price the
# dialog has stopped charging.
# ---------------------------------------------------------------------------
UPSELL = [
    ("up_band_eyebrow",       "Before you transfer · ninety seconds",           "قبل أن تحوّل · تسعون ثانية",                              NEW),
    ("up_band_p",             "{name} is the monthly work that puts your name inside Google's answers and ChatGPT's. Booked from this page it is {now} a month instead of {rack} — and nothing is charged today.",
                              "{name} هو العمل الشهري الذي يضع اسمك داخل إجابات جوجل وإجابات ChatGPT. وحجزه من هذه الصفحة بـ {now} شهرياً بدلاً من {rack} — ولا يُحتسب عليك شيء اليوم.",
                                                                                                                                           NEW),
    ("up_band_btn",           "Read it — {now} a month",                        "اقرأه — {now} شهرياً",                                    NEW),
    ("up_booked_h",           "{name} — booked at {now}/month",                 "{name} — محجوز بـ {now} شهرياً",                          NEW),
    ("up_booked_p",           "Locked at the price you were shown, and not charged today. It begins the month after your site goes live. Send me one message so it is on your file in writing — that message is your record of the price and the {months}-month guarantee.",
                              "مثبّت على السعر الذي عُرض عليك، ولا يُحتسب عليك اليوم. يبدأ في الشهر التالي لإطلاق موقعك. أرسل لي رسالة واحدة ليكون في ملفك كتابةً — تلك الرسالة هي سندك على السعر وعلى ضمان الـ {months} أشهر.",
                                                                                                                                           NEW),
    ("up_booked_wa",          "Confirm it on WhatsApp",                         "أكّده على واتساب",                                        NEW),
]


ALL = HTML + JS + UPSELL

# key -> Arabic. The builders ask for strings by key, never by position, so
# reordering a section above cannot silently repoint a sentence.
ALL_BY_KEY = {k: ar for k, _en, ar, _src in ALL}

if len(ALL_BY_KEY) != len(ALL):
    _dupes = sorted({k for k, *_ in ALL if [x[0] for x in ALL].count(k) > 1})
    raise SystemExit("duplicate key(s) in pay_ar_strings: " + ", ".join(_dupes))


# ---------------------------------------------------------------------------
# What the reviewer actually needs to look at
# ---------------------------------------------------------------------------
def review_list():
    """Only the NEW strings, English beside Arabic, for a native pass."""
    return [(k, en, ar) for k, en, ar, src in ALL if src == NEW]


def harvested():
    return [(k, en, ar, src) for k, en, ar, src in ALL if src != NEW]


def stats():
    n = len(ALL)
    new = len(review_list())
    return {"total": n, "new": new, "harvested": n - new,
            "pct_reviewed": round(100 * (n - new) / n)}


OPEN_QUESTIONS = [
    "smart-storefront-ar.html writes the deposit two ways on one page: "
    "'عربون 50%' and 'عربون ٥٠٪'. This table uses Western digits throughout, "
    "matching checkout-ar. The reviewer should settle which is intended and "
    "the storefront page should be made to match.",

    "'Pledged back to you, after delivery' uses تعهّد for pledge, which is the "
    "reviewed term on the storefront. The full sentence is new.",

    "Figures are printed the way pay.money_ar() prints them everywhere else: "
    "the number in Western digits, then ر.ع. after it - '97 ر.ع.' - with the "
    "number bidi-isolated so Arabic running text cannot reorder it. The seat "
    "page shows its figures from JavaScript, where there is no span to hang "
    "that on, so it uses the Unicode isolate characters instead. Same result, "
    "same reading order.",

    "The Thawani licence line names the Central Bank of Oman. Confirm the "
    "reviewer is happy with 'البنك المركزي العُماني' as the rendering, and "
    "that leaving 'Thawani' in Latin script is intended (checkout-ar does).",
]


if __name__ == "__main__":
    s = stats()
    print("strings: %(total)d   already reviewed: %(harvested)d (%(pct_reviewed)d%%)   "
          "NEW, needs a native pass: %(new)d" % s)
