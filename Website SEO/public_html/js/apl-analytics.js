// ==================== APL ANALYTICS ====================
//
// One shared measurement script for every page on aiprofitlab.io.
//
// Why this file exists: the tracking that mattered used to be written into the
// page templates, so changing what we measure meant editing a builder and
// regenerating ~375 pages. Everything here is behaviour that is identical on
// every page, so it belongs in one cached file - edit this, re-run the
// builders once to re-stamp the content hash, and the change is live.
//
// What is NOT here: the conversion events that only one page can fire -
// begin_checkout / add_payment_info (page_checkout.py), purchase
// (page_order.py), generate_lead, demo_* and simulator_* (the demo and
// simulator pages), filter_articles (the blog hubs), aiden_* (the chat
// widget). Those stay where the state they describe lives.
//
// Transport: the page's own gtag(). Every page already loads gtag.js and
// config's it to the one GA4 property, so this file deliberately carries no
// measurement id - GA_ID has exactly one home, in tools/v4/kit.py, and a copy
// here would be a second one to go stale.
//
// The four params set on every event (page_type, content_language,
// article_slug, page_path) are event-scoped custom dimensions. They must also
// be registered in GA4 (Admin > Custom definitions) before they show up in
// reports; unregistered, they are collected but not queryable.

(function () {
    'use strict';

    // ----------------------------------------------------------------------
    // Page classification
    //
    // pageType() is the single definition for the whole site. aiden-chat.js
    // used to carry its own copy and read it for the context it sends to the
    // backend; it now reads window.APLPage.pageType, so the two cannot drift.
    // That is also why this block sits at the top and publishes its API
    // synchronously: this file is loaded with `defer` in <head>, and Aiden
    // boots on window load + 900ms, so APLPage is always there in time.
    // ----------------------------------------------------------------------

    function pageType(path) {
        if (/\/blog\/(en|ar)\//.test(path)) return 'article';
        if (/\/academy\/(en|ar)\//.test(path)) return 'guide';
        if (/^\/(blog|blog-ar)\/?(index\.html)?$/.test(path)) return 'blog-hub';
        if (/^\/(academy|academy-ar)\/?(index\.html)?$/.test(path)) return 'academy-hub';
        if (/privacy|terms|legal|refund/.test(path)) return 'legal';
        if (/service|package/.test(path)) return 'services';
        if (/process/.test(path)) return 'process';
        if (/about/.test(path)) return 'about';
        if (/contact/.test(path)) return 'contact';
        if (/simulator|calculator/.test(path)) return 'tool';
        if (/demo/.test(path)) return 'demo';
        if (/offer|storefront|claim/.test(path)) return 'offer';
        // '/', '/index.html', '/en/', '/en/index.html' - and '/ar/', the
        // Arabic homepage, which the original of this test did not include:
        // build_v4 writes it to public_html/ar/index.html, so it fell past
        // every branch and was labelled the generic 'page'. Fixed here rather
        // than in a copy, which is the point of there being one classifier.
        if (/^\/(en\/|ar\/)?(index[\w-]*\.html)?$/.test(path)) return 'home';
        return 'page';
    }

    // The <html lang> every generated page carries, narrowed to the two
    // languages the site publishes. Falls back to the URL shape for the tail
    // of hand-maintained pages that predate the v4 head.
    function contentLanguage() {
        var attr = (document.documentElement.getAttribute('lang') || '').toLowerCase();
        if (attr.indexOf('ar') === 0) return 'ar';
        if (attr.indexOf('en') === 0) return 'en';
        return /(^\/ar\/|\/blog\/ar\/|\/academy\/ar\/|-ar(\.html)?\/?$|-ar\/)/.test(location.pathname)
            ? 'ar' : 'en';
    }

    // Articles are served both as /blog/en/<slug>.html and /blog/en/<slug>/,
    // so normalise both to <slug>. Empty on every other page type, which is
    // what makes article_slug safe to send on every event.
    function articleSlug(path) {
        if (!/\/blog\/(en|ar)\//.test(path)) return '';
        var last = path.replace(/\/+$/, '').split('/').pop() || '';
        return last.replace(/\.html$/, '');
    }

    var PATH = location.pathname;
    var TYPE = pageType(PATH);
    var LANG = contentLanguage();
    var SLUG = articleSlug(PATH);

    // ----------------------------------------------------------------------
    // Sending
    // ----------------------------------------------------------------------

    function hasGtag() {
        return typeof window.gtag === 'function';
    }

    // Event-scoped defaults: gtag merges these into every subsequent event,
    // including the ones fired from the page builders (begin_checkout,
    // generate_lead, aiden_open ...). That is the point - those events gain
    // page context without any of them being edited.
    if (hasGtag()) {
        try {
            window.gtag('set', {
                page_type: TYPE,
                content_language: LANG,
                article_slug: SLUG,
                page_path: PATH
            });
        } catch (e) { /* never let measurement break a page */ }
    }

    function track(name, params) {
        if (!hasGtag()) return;
        var p = params || {};
        // Re-stated per event rather than relied on from the `set` above, so
        // an event still carries its context if this file ever loads after a
        // page's own inline gtag call has already fired.
        p.page_type = TYPE;
        p.content_language = LANG;
        if (SLUG) p.article_slug = SLUG;
        try { window.gtag('event', name, p); } catch (e) { /* ok */ }
    }


    // ----------------------------------------------------------------------
    // Campaign attribution
    //
    // Why this exists: GA4 attributes a SESSION, and it forgets. Somebody who
    // scans the flyer on Tuesday, thinks about it, and comes back on Friday
    // through a Google search is a Google conversion as far as GA4's default
    // reporting is concerned - the flyer that actually did the work gets
    // nothing. For a campaign whose whole point is to find out which channel
    // is worth repeating, that is the one number that must not be wrong.
    //
    // So this keeps two touches in localStorage and never throws the first
    // one away:
    //
    //   first - the channel that introduced this person to the business.
    //           Written once, never overwritten, for the life of the storage.
    //   last  - the channel of the most recent CAMPAIGN or REFERRED visit.
    //           A direct visit deliberately does not overwrite it, which is
    //           the same "last non-direct" rule GA4 itself uses; otherwise
    //           every returning visitor would decay to `direct` and every
    //           channel would look useless.
    //
    // Both are read back by the seat-claim form, which posts them to the
    // ledger, so a row in the Google Sheet can finally say where the buyer
    // came from - and joined to BigQuery through the GA4 client id.
    // ----------------------------------------------------------------------

    var ATTR_KEY = 'apl_attr';
    var ATTR_SESSION_KEY = 'apl_attr_seen';

    // Ad-platform click ids. Their presence alone proves a paid click even
    // when the UTMs were dropped - a shortener, a QR reader that rewrites the
    // URL, or an app browser that strips the query on the way through.
    var CLICK_IDS = ['gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid', 'ttclid', 'li_fat_id', 'twclid'];

    // Referrer hosts worth naming. Anything not listed keeps its bare
    // hostname, which is more useful than bucketing it as 'other'.
    var REFERRER_MAP = [
        [/(^|\.)google\./i, 'google', 'organic'],
        [/(^|\.)bing\./i, 'bing', 'organic'],
        [/(^|\.)duckduckgo\./i, 'duckduckgo', 'organic'],
        [/(^|\.)(facebook|fb)\./i, 'facebook', 'social'],
        [/(^|\.)instagram\./i, 'instagram', 'social'],
        [/(^|\.)linkedin\.|(^|\.)lnkd\.in$/i, 'linkedin', 'social'],
        [/(^|\.)(whatsapp\.com|wa\.me)$/i, 'whatsapp', 'social'],
        [/(^|\.)t\.co$|(^|\.)(twitter|x)\.com$/i, 'twitter', 'social'],
        [/(^|\.)youtube\.|(^|\.)youtu\.be$/i, 'youtube', 'social'],
        [/(^|\.)tiktok\./i, 'tiktok', 'social'],
        [/(^|\.)t\.me$|(^|\.)telegram\./i, 'telegram', 'social']
    ];

    function store(key, value) {
        // Private mode, disabled storage, and a quota that is already full all
        // throw here. Attribution is worth less than the page working, so
        // every path through this file swallows it.
        try { window.localStorage.setItem(key, JSON.stringify(value)); } catch (e) { }
    }

    function load(key) {
        try {
            var raw = window.localStorage.getItem(key);
            return raw ? JSON.parse(raw) : null;
        } catch (e) { return null; }
    }

    function params() {
        try { return new URLSearchParams(location.search); } catch (e) { return null; }
    }

    // The touch this page view represents, or null for an unattributed visit
    // (typed the URL, opened a bookmark, followed a link from another page of
    // this same site).
    function currentTouch() {
        var q = params();
        var get = function (k) { return (q && q.get(k) || '').trim().slice(0, 100); };

        var clickId = '';
        var clickIdType = '';
        for (var i = 0; i < CLICK_IDS.length; i++) {
            var v = get(CLICK_IDS[i]);
            if (v) { clickId = v; clickIdType = CLICK_IDS[i]; break; }
        }

        var source = get('utm_source');
        var medium = get('utm_medium');
        var campaign = get('utm_campaign');

        var ref = document.referrer || '';
        var refHost = '';
        if (ref) {
            try {
                var u = new URL(ref);
                // A link from one page of this site to another is not a new
                // touch. Without this test every internal click would look
                // like a fresh visit from aiprofitlab.io.
                if (bareHost(u.hostname) !== bareHost(location.hostname)) refHost = bareHost(u.hostname);
            } catch (e) { }
        }

        // A click id with no UTMs still names its platform, so a stripped
        // query still lands in the right channel rather than in `direct`.
        if (!source && clickIdType) {
            if (clickIdType === 'fbclid') { source = 'facebook'; medium = medium || 'paid_social'; }
            else if (clickIdType === 'li_fat_id') { source = 'linkedin'; medium = medium || 'paid_social'; }
            else if (clickIdType === 'ttclid') { source = 'tiktok'; medium = medium || 'paid_social'; }
            else if (clickIdType === 'msclkid') { source = 'bing'; medium = medium || 'cpc'; }
            else { source = 'google'; medium = medium || 'cpc'; }
        }

        if (!source && refHost) {
            source = refHost;
            for (var j = 0; j < REFERRER_MAP.length; j++) {
                if (REFERRER_MAP[j][0].test(refHost)) {
                    source = REFERRER_MAP[j][1];
                    medium = medium || REFERRER_MAP[j][2];
                    break;
                }
            }
            medium = medium || 'referral';
        }

        if (!source) return null;

        return {
            source: source,
            medium: medium || '(none)',
            campaign: campaign || '(none)',
            content: get('utm_content'),
            term: get('utm_term'),
            click_id: clickId,
            click_id_type: clickIdType,
            referrer: refHost,
            landing_page: PATH.slice(0, 200),
            ts: new Date().toISOString()
        };
    }

    function readAttribution() {
        var saved = load(ATTR_KEY) || {};
        var touch = currentTouch();

        if (touch) {
            if (!saved.first) saved.first = touch;
            saved.last = touch;

            // touches counts CAMPAIGNS, not page views: without the session
            // guard, somebody who lands from the flyer and reads four pages
            // would look like four separate flyer scans, because the referrer
            // of page two is the site itself... which currentTouch() already
            // ignores, so in practice this guards the reload case and any
            // link that re-appends the UTMs.
            var seen = false;
            try { seen = window.sessionStorage.getItem(ATTR_SESSION_KEY) === '1'; } catch (e) { }
            if (!seen) {
                saved.touches = (saved.touches || 0) + 1;
                try { window.sessionStorage.setItem(ATTR_SESSION_KEY, '1'); } catch (e) { }
            }
            store(ATTR_KEY, saved);
        }

        return saved.first ? saved : null;
    }

    // Whole days between the first touch and now. This is the number that
    // says how long the flyer sat on a desk before anybody acted on it, and
    // it is only knowable because `first` is never overwritten.
    function daysSinceFirstTouch(attr) {
        if (!attr || !attr.first || !attr.first.ts) return null;
        var then = Date.parse(attr.first.ts);
        if (isNaN(then)) return null;
        return Math.max(0, Math.floor((Date.now() - then) / 86400000));
    }

    var ATTR = readAttribution();

    // User-scoped, not event-scoped, and deliberately only three of them.
    // GA4's free tier allows 25 user-scoped custom dimensions and 50
    // event-scoped ones, and hanging the full attribution object off every
    // event would burn the event-scoped budget to re-state a fact that does
    // not change between events. These three answer "which channel produced
    // this person", which is the campaign question.
    if (ATTR && hasGtag()) {
        try {
            window.gtag('set', 'user_properties', {
                first_source: ATTR.first.source,
                first_medium: ATTR.first.medium,
                first_campaign: ATTR.first.campaign
            });
        } catch (e) { }
    }

    // ----------------------------------------------------------------------
    // Scroll depth
    //
    // GA4 enhanced measurement fires exactly one scroll event, at 90%. That
    // tells you almost nothing about where a long article loses people, so
    // this reports the usual quartiles instead, under its own event name -
    // `scroll_depth`, not `scroll` - so the two never mix in a report.
    // ----------------------------------------------------------------------

    var MILESTONES = [25, 50, 75, 100];
    var fired = {};
    var maxScroll = 0;
    var ticking = false;

    function scrollPercent() {
        var doc = document.documentElement;
        var scrollable = doc.scrollHeight - window.innerHeight;
        // A page shorter than the viewport has been seen in full the moment
        // it paints. max_scroll is therefore 100, but no milestone fires:
        // there was no scrolling to measure, and counting four milestones on
        // a page nobody scrolled would flatter every short page in the report.
        if (scrollable <= 0) return -1;
        var y = window.scrollY || doc.scrollTop || 0;
        return Math.max(0, Math.min(100, Math.round((y / scrollable) * 100)));
    }

    function measureScroll() {
        var pct = scrollPercent();
        if (pct < 0) { maxScroll = 100; return; }
        if (pct > maxScroll) maxScroll = pct;
        for (var i = 0; i < MILESTONES.length; i++) {
            var m = MILESTONES[i];
            if (maxScroll >= m && !fired[m]) {
                fired[m] = true;
                track('scroll_depth', { percent_scrolled: m });
            }
        }
    }

    function onScroll() {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(function () {
            ticking = false;
            measureScroll();
        });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    measureScroll();

    // ----------------------------------------------------------------------
    // Time on page
    //
    // Accumulated VISIBLE time, not wall-clock since load: a tab left open in
    // the background for an hour did not hold anyone's attention for an hour.
    // ----------------------------------------------------------------------

    var visibleMs = 0;
    var visibleSince = document.visibilityState === 'visible' ? Date.now() : 0;

    function accumulate() {
        if (visibleSince) {
            visibleMs += Date.now() - visibleSince;
            visibleSince = 0;
        }
    }

    function dwellSeconds() {
        var total = visibleMs + (visibleSince ? Date.now() - visibleSince : 0);
        return Math.round(total / 1000);
    }

    // ----------------------------------------------------------------------
    // Exit intent
    //
    // The pointer leaving through the TOP edge of the viewport - toward the
    // tab strip, the address bar or the close button. Only meaningful with a
    // mouse; on touch it simply stays false, which is the honest answer.
    // ----------------------------------------------------------------------

    var exitIntent = false;

    document.addEventListener('mouseout', function (e) {
        if (exitIntent) return;
        if (e.relatedTarget || e.toElement) return;   // still inside the document
        if ((e.clientY || 0) > 0) return;             // left sideways or downward
        exitIntent = true;
    }, true);

    // ----------------------------------------------------------------------
    // page_exit
    //
    // The one number GA4 measures worst. Engaged-time on the LAST page of a
    // session is inferred from a heartbeat that stops arriving, so the page a
    // visitor actually left from - the drop-off page, the one worth fixing -
    // is exactly where the built-in figure is least trustworthy.
    //
    // Fires ONCE per page view, on the first transition to hidden. A tab
    // switch is that transition, so this is deliberately not re-armed when
    // the visitor comes back: the interesting measurement is how far they got
    // before their attention first left, and re-firing would turn one page
    // view into a stream of events that no report can average sensibly.
    //
    // transport_type:'beacon' is what makes it survive unload - gtag hands
    // the hit to navigator.sendBeacon, which the browser delivers after the
    // document is gone, instead of an image request the unload cancels.
    // ----------------------------------------------------------------------

    var exitSent = false;

    function sendExit() {
        if (exitSent) return;
        exitSent = true;
        accumulate();
        track('page_exit', {
            dwell_seconds: dwellSeconds(),
            max_scroll: maxScroll,
            exit_intent: exitIntent,
            transport_type: 'beacon'
        });
    }

    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') {
            sendExit();
        } else if (!visibleSince) {
            visibleSince = Date.now();
        }
    });

    // Backstop, same once-only flag so it cannot double-count: Safari has
    // historically dropped straight into bfcache on navigation without a
    // visibilitychange, and pagehide is the event that always fires there.
    window.addEventListener('pagehide', sendExit);

    // ----------------------------------------------------------------------
    // CTA and outbound clicks
    //
    // Classified by DESTINATION, not by class name. The pinned WhatsApp
    // button is `.top-wa` on the v4 pages and the articles, `.fab` on the
    // older skin, `.btn-wa` inline and a bare icon link in the footer - four
    // selectors for one intent, and a fifth the next page will invent. The
    // href is the thing that cannot drift, so that is what is matched, and
    // the selector only decides the cta_location label.
    //
    // Names are deliberately not `click`: GA4 enhanced measurement already
    // fires `click` with outbound:true for external links, and reusing the
    // name would blend two differently-defined counts in one report.
    // ----------------------------------------------------------------------

    var WA_HOSTS = /(^|\.)(whatsapp\.com|wa\.me)$/i;

    function bareHost(h) {
        return (h || '').toLowerCase().replace(/^www\./, '');
    }

    function ctaLocation(a) {
        if (a.closest('.fab, .top-wa')) return 'fab';
        if (a.closest('header, .hdr, .nav')) return 'header';
        if (a.closest('footer, .ftr')) return 'footer';
        return 'inline';
    }

    function linkText(a) {
        var t = (a.getAttribute('aria-label') || a.textContent || '').replace(/\s+/g, ' ').trim();
        return t.slice(0, 100);
    }

    document.addEventListener('click', function (e) {
        var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
        if (!a) return;

        var raw = a.getAttribute('href') || '';
        if (!raw || raw.charAt(0) === '#') return;

        if (/^tel:/i.test(raw)) {
            track('cta_click', {
                cta_type: 'phone', cta_location: ctaLocation(a),
                link_url: raw, link_text: linkText(a)
            });
            return;
        }
        if (/^mailto:/i.test(raw)) {
            track('cta_click', {
                cta_type: 'email', cta_location: ctaLocation(a),
                link_url: raw, link_text: linkText(a)
            });
            return;
        }

        // Anything else is only interesting if it resolves to another origin.
        var url;
        try { url = new URL(a.href, location.href); } catch (err) { return; }
        if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
        if (bareHost(url.hostname) === bareHost(location.hostname)) return;

        if (WA_HOSTS.test(bareHost(url.hostname))) {
            track('cta_click', {
                cta_type: 'whatsapp', cta_location: ctaLocation(a),
                link_url: url.href.slice(0, 300), link_text: linkText(a)
            });
            return;
        }

        // One click is one event: a WhatsApp link is a CTA and never also an
        // outbound_click, so the two counts stay independently meaningful.
        track('outbound_click', {
            link_domain: bareHost(url.hostname),
            link_url: url.href.slice(0, 300),
            link_text: linkText(a)
        });
    }, true);


    // ----------------------------------------------------------------------
    // Meta Pixel - OFF until there is a real id
    //
    // Paste the pixel id from Meta Events Manager (Data sources > your pixel,
    // a 15-16 digit number) between the quotes below, re-run the builders and
    // tools/stamp_analytics_version.py, and it is live on all ~368 pages. An
    // empty string means not one byte is sent to Meta and no request is made -
    // which is the correct state until Nahid actually has a pixel, because a
    // half-configured pixel reports conversions it cannot attribute and is
    // worse than none.
    //
    // WHY IT IS HERE rather than in the page templates: this file is already
    // on every page and is content-hash versioned, so turning the pixel on is
    // a one-line edit plus a re-stamp, instead of a change to three separate
    // head blocks that would then be free to drift apart.
    //
    // The conversion events are NOT wired by hand into the storefront and pay
    // pages. Those pages already announce everything they do through gtag, so
    // this listens to the dataLayer instead and translates. Nothing in a page
    // has to know the pixel exists, and a page added later is covered for
    // free.
    // ----------------------------------------------------------------------

    var META_PIXEL_ID = '';

    // Site event -> Meta standard event. Only real commercial intent is
    // mapped: sending Meta every scroll milestone trains its optimiser on
    // noise and burns budget finding people who scroll.
    var META_EVENTS = {
        claim_submitted: 'Lead',
        seat_payment_started: 'InitiateCheckout',
        seat_paid: 'Purchase',
        generate_lead: 'Lead',
        begin_checkout: 'InitiateCheckout',
        purchase: 'Purchase',
        add_to_cart: 'AddToCart'
    };

    function bootMetaPixel(id) {
        /* eslint-disable */
        !function (f, b, e, v, n, t, s) {
            if (f.fbq) return; n = f.fbq = function () {
                n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments)
            };
            if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
            t = b.createElement(e); t.async = !0; t.src = v;
            s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s)
        }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
        /* eslint-enable */

        window.fbq('init', id);
        window.fbq('track', 'PageView');

        // Mirror gtag events onto the pixel by watching the dataLayer every
        // gtag call already pushes to. Wrapping push is reversible and keeps
        // the original's return value, so gtag behaves exactly as before if
        // anything in here throws.
        try {
            var dl = window.dataLayer = window.dataLayer || [];
            var push = dl.push;
            dl.push = function () {
                var result = push.apply(this, arguments);
                try {
                    var a = arguments[0];
                    if (a && a[0] === 'event' && META_EVENTS[a[1]]) {
                        var p = a[2] || {};
                        var payload = {};
                        // Meta wants value+currency on a Purchase to report
                        // revenue; sending a value without a currency makes it
                        // guess, and it guesses USD.
                        if (typeof p.value === 'number') {
                            payload.value = p.value;
                            payload.currency = p.currency || 'OMR';
                        }
                        window.fbq('track', META_EVENTS[a[1]], payload);
                    }
                } catch (e) { /* never break gtag */ }
                return result;
            };
        } catch (e) { }
    }

    if (META_PIXEL_ID) {
        try { bootMetaPixel(META_PIXEL_ID); } catch (e) { }
    }

    // ----------------------------------------------------------------------
    // Public API - what aiden-chat.js reads instead of keeping its own copy.
    // ----------------------------------------------------------------------

    // GA4's own ids, read out of the tag rather than reinvented. `client_id`
    // is the cookie that BigQuery keys every event on, so a lead row carrying
    // it can be joined to everything that person did before they filled the
    // form in - which is the whole reason the export exists.
    //
    // gtag('get', ...) is ASYNCHRONOUS and answers only once gtag.js has
    // loaded. It also never calls back at all if the script was blocked, so
    // this resolves with empty strings on a timer rather than leaving a form
    // submit waiting forever on an ad blocker.
    function gaIds(cb, timeoutMs) {
        var out = { client_id: '', session_id: '' };
        var done = false;
        var pending = 2;

        function finish() {
            if (done) return;
            done = true;
            cb(out);
        }

        var timer = setTimeout(finish, timeoutMs || 1200);

        function got(key) {
            return function (value) {
                out[key] = value == null ? '' : String(value);
                if (--pending === 0) { clearTimeout(timer); finish(); }
            };
        }

        if (!hasGtag()) { clearTimeout(timer); return finish(); }
        try {
            // The measurement id is read back off the loaded tag rather than
            // written here: GA_ID has one home, in tools/v4/kit.py, and a
            // second copy in this file is a second one to go stale.
            var id = measurementId();
            if (!id) { clearTimeout(timer); return finish(); }
            window.gtag('get', id, 'client_id', got('client_id'));
            window.gtag('get', id, 'session_id', got('session_id'));
        } catch (e) { clearTimeout(timer); finish(); }
    }

    // Recovered from the gtag.js script tag the page already carries.
    function measurementId() {
        var tags = document.querySelectorAll('script[src*="googletagmanager.com/gtag/js"]');
        for (var i = 0; i < tags.length; i++) {
            var m = /[?&]id=(G-[A-Z0-9]+)/i.exec(tags[i].getAttribute('src') || '');
            if (m) return m[1];
        }
        return '';
    }

    window.APLPage = {
        pageType: pageType,
        type: TYPE,
        language: LANG,
        slug: SLUG,
        path: PATH,
        track: track,

        // The campaign that produced this visitor, or null if nothing ever
        // attributed them. Shape: { first: {...}, last: {...}, touches: n }.
        attribution: ATTR,
        daysSinceFirstTouch: function () { return daysSinceFirstTouch(ATTR); },

        // A flat, ledger-shaped view of the same thing. Every value is a
        // string, so it can be posted straight into a spreadsheet column
        // without a null turning into the text "null".
        attributionFields: function () {
            var f = ATTR && ATTR.first ? ATTR.first : null;
            var l = ATTR && ATTR.last ? ATTR.last : null;
            var days = daysSinceFirstTouch(ATTR);
            return {
                firstSource: f ? f.source : '',
                firstMedium: f ? f.medium : '',
                firstCampaign: f ? f.campaign : '',
                firstLandingPage: f ? f.landing_page : '',
                firstSeenAt: f ? f.ts : '',
                lastSource: l ? l.source : '',
                lastMedium: l ? l.medium : '',
                lastCampaign: l ? l.campaign : '',
                clickId: l && l.click_id ? l.click_id : (f && f.click_id ? f.click_id : ''),
                clickIdType: l && l.click_id_type ? l.click_id_type : (f && f.click_id_type ? f.click_id_type : ''),
                touches: ATTR && ATTR.touches ? String(ATTR.touches) : '',
                daysToClaim: days === null ? '' : String(days)
            };
        },

        gaIds: gaIds
    };
})();
