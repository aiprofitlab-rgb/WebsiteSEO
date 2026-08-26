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
    // Public API - what aiden-chat.js reads instead of keeping its own copy.
    // ----------------------------------------------------------------------

    window.APLPage = {
        pageType: pageType,
        type: TYPE,
        language: LANG,
        slug: SLUG,
        path: PATH,
        track: track
    };
})();
