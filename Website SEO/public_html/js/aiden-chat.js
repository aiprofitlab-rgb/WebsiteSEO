// ==================== AIDEN CHAT WIDGET ====================
//
// One self-contained chat widget for the whole site.
//
// Design notes worth knowing before editing:
//
// * Everything lives in a shadow root. The site ships three different CSS
//   worlds - Tailwind CDN on the legacy pages, the hand-rolled v4 brand skin,
//   and Cairo/RTL on the Arabic pages - and the old widget inherited from
//   whichever one it landed in, which is why it looked different (and wrong)
//   depending on the page. Inside a shadow root nothing leaks either way, so
//   the widget looks identical everywhere and cannot disturb the page.
//
// * The skin is derived from the page's own background luminance, so the
//   widget reads as part of a cream v4 page and part of a dark legacy page
//   without either being a special case.
//
// * The launcher measures other fixed bottom-corner elements (the WhatsApp
//   .fab on the v4 pages and the blog hubs) and stacks above them instead of
//   sitting on top of them.
//
// * Pages that still ship the old inline widget markup have it removed on
//   mount, so there is exactly one Aiden on the page and it is this one.
//
// Public API is unchanged: window.aidenChat.init / toggle / send.

(function () {
    'use strict';

    var API = 'https://aiden-backend-aiden.up.railway.app/chat';
    // Where the widget sends a visitor when the backend cannot answer.
    var WHATSAPP_URL = 'https://api.whatsapp.com/send?phone=96899245250' +
        '&text=' + encodeURIComponent('Hello Nahid, I have a question about my business.');
    var SITE_HOST = 'aiprofitlab.io';
    var REQUEST_TIMEOUT_MS = 30000;

    // Visitor identity keys are the originals: renaming them would reset every
    // existing visitor's history and visit count.
    var K_ID = 'aidenVisitorId';
    var K_COUNT = 'aidenVisitCount';
    var K_FIRST = 'aidenFirstVisit';
    var K_LAST = 'aidenLastVisit';
    var K_TRANSCRIPT = 'aidenTranscript';
    var K_PAGES = 'aidenPagesSeen';
    var K_EMAIL = 'aidenVisitorEmail';

    var TRANSCRIPT_TTL_DAYS = 30;   // older than this and we greet as new
    var TRANSCRIPT_MAX = 40;        // messages kept locally
    var HISTORY_TO_SEND = 8;        // messages replayed to the backend
    var MAX_MSG_CHARS = 2000;

    var isAr = document.documentElement.lang === 'ar' ||
        (document.documentElement.getAttribute('dir') || '').toLowerCase() === 'rtl';
    var isRtl = (document.documentElement.getAttribute('dir') || '').toLowerCase() === 'rtl' || isAr;

    function t(en, ar) { return isAr ? ar : en; }

    // ---------- storage (private mode must never break the widget) ----------

    function lsGet(key, fallback) {
        try {
            var v = localStorage.getItem(key);
            return v === null ? fallback : v;
        } catch (e) { return fallback; }
    }

    function lsSet(key, value) {
        try { localStorage.setItem(key, value); } catch (e) { /* best-effort */ }
    }

    function lsJson(key, fallback) {
        try {
            var raw = localStorage.getItem(key);
            if (!raw) return fallback;
            var parsed = JSON.parse(raw);
            return parsed === null || parsed === undefined ? fallback : parsed;
        } catch (e) { return fallback; }
    }

    // ---------- visitor ----------

    function visitorId() {
        var id = lsGet(K_ID, '');
        if (!id) {
            id = 'visitor_' + Date.now() + '_' + Math.random().toString(36).slice(2, 11);
            lsSet(K_ID, id);
            lsSet(K_FIRST, new Date().toISOString());
        }
        return id;
    }

    /** Whole days between two moments, or null when we have no earlier one. */
    function daysSince(iso) {
        if (!iso) return null;
        var then = Date.parse(iso);
        if (isNaN(then)) return null;
        return Math.max(0, Math.floor((Date.now() - then) / 86400000));
    }

    /**
     * Which visit is this, and how long since the last one?
     *
     * A visit is a browser session, not a page view: counting page views would
     * make someone who reads four articles in one sitting look like a visitor
     * returning for the fourth time, and they would be greeted with "good to
     * see you back" on their second click. The answer is computed once per tab
     * session and cached there, so every page in the session agrees.
     */
    var priorVisit = { count: 1, days: null };

    function openVisit() {
        try {
            var cached = sessionStorage.getItem('aidenVisit');
            if (cached) return JSON.parse(cached);
        } catch (e) { /* fall through and count this page view as a visit */ }

        var previousCount = parseInt(lsGet(K_COUNT, '0'), 10) || 0;
        var info = { count: previousCount + 1, days: daysSince(lsGet(K_LAST, '')) };

        lsSet(K_COUNT, String(info.count));
        lsSet(K_LAST, new Date().toISOString());
        try { sessionStorage.setItem('aidenVisit', JSON.stringify(info)); } catch (e) { /* ok */ }
        return info;
    }

    // ---------- what the visitor is looking at ----------

    function pageTitle() {
        var h1 = document.querySelector('h1');
        // innerText, not textContent: headlines here are broken with <br>, and
        // textContent glues the halves together ("the problem.I build").
        var text = h1 ? (h1.innerText || h1.textContent || '') : '';
        if (!text.trim()) text = document.title || '';
        return text.replace(/\s+/g, ' ').trim().slice(0, 160);
    }

    function pageDescription() {
        var meta = document.querySelector('meta[name="description"]');
        return meta ? (meta.getAttribute('content') || '').slice(0, 300) : '';
    }

    // The section headings are the cheapest honest summary of a page, and they
    // matter most on pages the backend's index does not know about yet.
    function pageHeadings() {
        var out = [];
        var nodes = document.querySelectorAll('h2');
        for (var i = 0; i < nodes.length && out.length < 8; i++) {
            var text = (nodes[i].textContent || '').replace(/\s+/g, ' ').trim();
            if (text.length >= 3 && text.length <= 120) out.push(text);
        }
        return out;
    }

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
        if (/^\/(en\/)?(index[\w-]*\.html)?$/.test(path)) return 'home';
        return 'page';
    }

    // Trail of pages in this tab session (what Aiden calls "the journey").
    function trackJourney() {
        var trail = [];
        try { trail = JSON.parse(sessionStorage.getItem('aidenJourney') || '[]'); } catch (e) { trail = []; }
        if (!Array.isArray(trail)) trail = [];
        var here = location.pathname;
        if (!trail.length || trail[trail.length - 1].path !== here) {
            trail.push({ path: here, title: pageTitle().slice(0, 120) });
            if (trail.length > 20) trail.shift();
            try { sessionStorage.setItem('aidenJourney', JSON.stringify(trail)); } catch (e) { /* ok */ }
        }
        return trail;
    }

    // Pages seen across *all* visits, so a returning visitor is recognised as
    // someone who already read the pricing page last week.
    function trackPagesSeen() {
        var seen = lsJson(K_PAGES, []);
        if (!Array.isArray(seen)) seen = [];
        var here = location.pathname;
        seen = seen.filter(function (p) { return p && p.path !== here; });
        seen.push({ path: here, title: pageTitle().slice(0, 120), at: Date.now() });
        if (seen.length > 25) seen = seen.slice(-25);
        lsSet(K_PAGES, JSON.stringify(seen));
        return seen;
    }

    var pagesBeforeThisOne = lsJson(K_PAGES, []);

    // ---------- engagement ----------

    var pageOpenedAt = Date.now();
    var maxScroll = 0;

    function trackScroll() {
        var doc = document.documentElement;
        var scrollable = doc.scrollHeight - window.innerHeight;
        if (scrollable <= 0) return;
        var pct = Math.round(((window.scrollY || doc.scrollTop) / scrollable) * 100);
        if (pct > maxScroll) maxScroll = Math.min(100, pct);
    }

    function behaviour() {
        return {
            secondsOnPage: Math.round((Date.now() - pageOpenedAt) / 1000),
            scrollDepth: maxScroll,
            referrer: document.referrer && document.referrer.indexOf(SITE_HOST) === -1
                ? document.referrer.slice(0, 200)
                : ''
        };
    }

    // ---------- transcript that survives across visits ----------
    //
    // The backend keeps conversation memory in process, which is right for a
    // live conversation but gone after a redeploy or a night's sleep. Keeping
    // the transcript in the visitor's own browser is what lets Aiden pick up a
    // thread from last week - and it is replayed to the backend on the next
    // message so the model sees the same history the visitor can see.

    function loadTranscript() {
        var saved = lsJson(K_TRANSCRIPT, null);
        if (!saved || !Array.isArray(saved.messages) || !saved.messages.length) return null;
        var age = Date.now() - (saved.updatedAt || 0);
        if (age > TRANSCRIPT_TTL_DAYS * 86400000) {
            lsSet(K_TRANSCRIPT, '');
            return null;
        }
        return saved;
    }

    var transcript = loadTranscript();
    var priorMessages = transcript ? transcript.messages.slice() : [];
    var priorContext = transcript ? {
        page: transcript.lastPage || '',
        pageTitle: transcript.lastPageTitle || '',
        updatedAt: transcript.updatedAt || 0
    } : null;

    function saveTranscript(messages) {
        var trimmed = messages.slice(-TRANSCRIPT_MAX).map(function (m) {
            return { role: m.role, text: String(m.text).slice(0, MAX_MSG_CHARS) };
        });
        lsSet(K_TRANSCRIPT, JSON.stringify({
            messages: trimmed,
            updatedAt: Date.now(),
            lastPage: location.pathname,
            lastPageTitle: pageTitle()
        }));
    }

    function clearTranscript() {
        lsSet(K_TRANSCRIPT, '');
        priorMessages = [];
        priorContext = null;
    }

    /** The visitor's last question, used for the "last time we talked about" line. */
    function lastTopic() {
        for (var i = priorMessages.length - 1; i >= 0; i--) {
            if (priorMessages[i].role === 'user') return priorMessages[i].text;
        }
        return '';
    }

    function relativeWhen(ms) {
        var days = Math.floor((Date.now() - ms) / 86400000);
        if (days <= 0) return t('earlier today', 'في وقت سابق اليوم');
        if (days === 1) return t('yesterday', 'أمس');
        if (days < 7) return t(days + ' days ago', 'قبل ' + days + ' أيام');
        if (days < 14) return t('last week', 'الأسبوع الماضي');
        if (days < 60) return t(Math.round(days / 7) + ' weeks ago', 'قبل ' + Math.round(days / 7) + ' أسابيع');
        return t('a while back', 'منذ فترة');
    }

    // ---------- safe rendering ----------

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Only same-site links are ever rendered as anchors. Anything else stays as
    // plain text, so a malformed or injected URL can never become javascript:.
    function safeUrl(url) {
        if (/^\/(?!\/)/.test(url)) return url;
        if (/^https?:\/\/([\w-]+\.)?aiprofitlab\.io(\/|$)/i.test(url)) return url;
        return null;
    }

    // Minimal markdown: links, bold, lists, line breaks. Input is escaped
    // first, so no raw HTML from the model can reach the DOM.
    function renderMarkdown(text) {
        var html = escapeHtml(text);

        html = html.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, function (match, label, url) {
            var href = safeUrl(url);
            if (!href) return label;
            return '<a class="lnk" href="' + href + '">' + label + '</a>';
        });

        html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/(?:^|\n)[-*]\s+([^\n]+)/g, '\n<span class="li">$1</span>');
        html = html.replace(/\n{2,}/g, '<br><br>').replace(/\n/g, '<br>');
        return html;
    }

    // ---------- icons ----------

    var ICON_MARK =
        '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
        '<path d="M6 5h20a3 3 0 0 1 3 3v13a3 3 0 0 1-3 3H15l-7 5.5V24H6a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3z" ' +
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>' +
        '<path d="M16 9.2l1.55 3.9 3.9 1.55-3.9 1.55L16 20.2l-1.55-3.9-3.9-1.55 3.9-1.55z" fill="currentColor"/>' +
        '</svg>';

    var ICON_SEND =
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
        '<path d="M3.6 11.3 20 4.2c.8-.35 1.6.45 1.25 1.25l-7.1 16.4c-.36.83-1.56.78-1.85-.08l-2.2-6.45-6.45-2.2c-.86-.29-.91-1.49-.05-1.82z" ' +
        'fill="currentColor"/></svg>';

    var ICON_CLOSE =
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
        '<path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

    var ICON_ARROW =
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" class="chevron">' +
        '<path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" stroke-linejoin="round"/></svg>';

    // ---------- greeting + page-aware suggestions ----------

    function pageGreeting(type, returning) {
        var topic = pageTitle().slice(0, 70);
        switch (type) {
            case 'services':
                return t('You are looking at the packages. Tell me roughly what your business does and I will say which one actually fits.',
                    'أنت تطّلع على الباقات. أخبرني باختصار عن طبيعة عملك وسأقول لك أي باقة تناسبك فعلاً.');
            case 'process':
                return t('This page walks through how a build runs end to end. Which part would you like me to expand on?',
                    'هذه الصفحة تشرح كيف يسير المشروع من البداية للنهاية. أي جزء تحب أن أوضحه أكثر؟');
            case 'contact':
                return t('Happy to answer here first — most questions do not need a call. What would you like to know?',
                    'يسعدني الإجابة هنا أولاً — أغلب الأسئلة لا تحتاج مكالمة. ماذا تريد أن تعرف؟');
            case 'about':
                return t('This page is about who we are. Ask me anything about how we work or who we build for.',
                    'هذه الصفحة تعرّفك بنا. اسألني عن طريقة عملنا أو عن نوع العملاء الذين نخدمهم.');
            case 'guide':
                return t('Reading "' + topic + '"? Ask me anything in it, or how it would apply to your own business.',
                    'تقرأ "' + topic + '"؟ اسألني عن أي نقطة فيه، أو كيف يمكن تطبيقه في عملك.');
            case 'article':
                return t('Ask me anything about this article, or how the idea would work in your business.',
                    'اسألني عن أي شيء في هذا المقال، أو كيف تعمل الفكرة في مجالك.');
            case 'blog-hub':
            case 'academy-hub':
                return t('Tell me what you are trying to solve and I will point you to the right piece.',
                    'أخبرني ما الذي تحاول حلّه وسأدلّك على المقال المناسب.');
            case 'tool':
                return t('Want help reading these numbers? Tell me about your business and I will walk you through them.',
                    'تريد مساعدة في قراءة هذه الأرقام؟ أخبرني عن عملك وسأشرحها لك.');
            case 'demo':
                return t('This is a live demo. Ask me how the same system would run inside your business.',
                    'هذا عرض حي. اسألني كيف يعمل النظام نفسه داخل شركتك.');
            case 'offer':
                return t('Questions about this offer? I can tell you exactly what is included and what it costs.',
                    'لديك أسئلة حول هذا العرض؟ يمكنني إخبارك بالضبط بما يتضمنه وبتكلفته.');
            case 'legal':
                return t('Ask me anything on this page and I will keep it plain.',
                    'اسألني عن أي بند في هذه الصفحة وسأشرحه ببساطة.');
            default:
                // A returning visitor already knows who Aiden is; introducing
                // yourself to someone on their third visit is the tell of a bot.
                return returning
                    ? t('What can I help with today?', 'كيف أساعدك اليوم؟')
                    : t('I am Aiden. Tell me what your business does and I will tell you where AI would actually pay off.',
                        'أنا أيدن. أخبرني بما تعمله شركتك وسأخبرك أين يمكن للذكاء الاصطناعي أن يحقق عائداً فعلياً.');
        }
    }

    var SUGGESTIONS = {
        services: [
            ['What is included in each package?', 'ماذا تتضمن كل باقة؟'],
            ['Which package fits a small business?', 'أي باقة تناسب شركة صغيرة؟'],
            ['What are the ongoing costs?', 'ما هي التكاليف الشهرية؟']
        ],
        process: [
            ['How long does a build take?', 'كم يستغرق تنفيذ المشروع؟'],
            ['What do you need from me?', 'ماذا تحتاج مني؟'],
            ['What happens after launch?', 'ماذا يحدث بعد الإطلاق؟']
        ],
        contact: [
            ['What happens on a strategy call?', 'ماذا يحدث في المكالمة الاستراتيجية؟'],
            ['How much does this cost?', 'كم تبلغ التكلفة؟'],
            ['Do you work outside Oman?', 'هل تعملون خارج عُمان؟']
        ],
        about: [
            ['Who do you usually work with?', 'مع من تعملون عادة؟'],
            ['What makes you different?', 'ما الذي يميزكم؟'],
            ['Show me what you build', 'أرني ما الذي تبنونه']
        ],
        home: [
            ['What exactly do you build?', 'ما الذي تبنونه بالضبط؟'],
            ['How much does it cost?', 'كم تبلغ التكلفة؟'],
            ['Would this work for my business?', 'هل يناسب هذا مجال عملي؟']
        ],
        article: [
            ['Summarise this for me', 'لخّص لي هذا المقال'],
            ['How would this work in my business?', 'كيف يُطبَّق هذا في عملي؟'],
            ['What would it cost to build?', 'كم تكلفة بناء هذا؟']
        ],
        guide: [
            ['Explain this more simply', 'اشرح لي هذا ببساطة أكثر'],
            ['How do I start with this?', 'كيف أبدأ بهذا؟'],
            ['What does it cost to build?', 'كم تكلفة بنائه؟']
        ],
        'blog-hub': [
            ['Find me something on WhatsApp automation', 'اعرض لي مقالاً عن أتمتة واتساب'],
            ['What should I read first?', 'بماذا أبدأ القراءة؟'],
            ['Do you have anything on pricing?', 'هل لديكم مقال عن التسعير؟']
        ],
        'academy-hub': [
            ['Which guide should I start with?', 'بأي دليل أبدأ؟'],
            ['I am new to AI — where do I begin?', 'أنا مبتدئ في الذكاء الاصطناعي — من أين أبدأ؟'],
            ['What can AI do for my team?', 'ماذا يمكن للذكاء الاصطناعي أن يفعل لفريقي؟']
        ],
        tool: [
            ['What do these numbers mean?', 'ماذا تعني هذه الأرقام؟'],
            ['Are these assumptions realistic?', 'هل هذه الافتراضات واقعية؟'],
            ['What would fix this for me?', 'ما الحل المناسب لي؟']
        ],
        demo: [
            ['Can I get this for my business?', 'هل يمكنني الحصول على هذا لعملي؟'],
            ['How long does it take to build?', 'كم يستغرق بناؤه؟'],
            ['What does it cost?', 'كم يكلّف؟']
        ],
        offer: [
            ['What exactly is included?', 'ما الذي يتضمنه بالضبط؟'],
            ['Is there a monthly fee?', 'هل هناك رسوم شهرية؟'],
            ['How do I claim this?', 'كيف أحصل على هذا العرض؟']
        ],
        legal: [
            ['Explain this in plain language', 'اشرح لي هذا بلغة بسيطة'],
            ['How is my data handled?', 'كيف تُعالج بياناتي؟'],
            ['Talk to a human', 'أريد التحدث مع شخص']
        ],
        page: [
            ['What do you actually do?', 'ما الذي تقومون به فعلياً؟'],
            ['How much does it cost?', 'كم تبلغ التكلفة؟'],
            ['Would this work for my business?', 'هل يناسب هذا عملي؟']
        ]
    };

    function suggestionsFor(type) {
        var list = SUGGESTIONS[type] || SUGGESTIONS.page;
        return list.map(function (pair) { return t(pair[0], pair[1]); });
    }

    // ---------- skin ----------

    function parseColor(value) {
        var m = /rgba?\(([^)]+)\)/.exec(value || '');
        if (!m) return null;
        var parts = m[1].split(',').map(function (n) { return parseFloat(n); });
        if (parts.length >= 4 && parts[3] === 0) return null;   // fully transparent
        return { r: parts[0], g: parts[1], b: parts[2] };
    }

    /**
     * Is the page dark? Read the first opaque background walking up from body.
     * A page with no declared background is white by default, so "no answer"
     * means light.
     */
    function pageIsDark() {
        var nodes = [document.body, document.documentElement];
        for (var i = 0; i < nodes.length; i++) {
            if (!nodes[i]) continue;
            var colour = parseColor(getComputedStyle(nodes[i]).backgroundColor);
            if (!colour) continue;
            var luminance = (0.299 * colour.r + 0.587 * colour.g + 0.114 * colour.b) / 255;
            return luminance < 0.5;
        }
        return false;
    }

    // Brand tokens, from the AI Profit Lab brand book: deep teal ground,
    // amber accent, cream paper.
    var CSS = [
        ':host{',
        '  --teal-950:#072B22; --teal-900:#0A3D30; --teal:#0F6E56; --teal-600:#158268;',
        '  --amber:#BA7517; --amber-bright:#D89234;',
        '  --sans:"IBM Plex Sans","Cairo",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;',
        '  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;',
        '  --ease:cubic-bezier(.22,.7,.25,1);',
        '  --gap:20px;',
        '  --bottom:20px;',
        '  position:fixed; bottom:var(--bottom); z-index:2147483000;',
        '  font-family:var(--sans); line-height:1.55;',
        '  -webkit-font-smoothing:antialiased;',
        '}',
        ':host([hidden]){display:none}',
        ':host(.ltr){right:var(--gap); left:auto}',
        ':host(.rtl){left:var(--gap); right:auto}',

        /* ---- light skin (cream pages) ---- */
        ':host{',
        '  --paper:#F5F2EA; --surface:#FFFFFF; --ink:#232B26; --muted:#5F6B62;',
        '  --line:#E3DCCB; --field:#FFFFFF;',
        '  --bot-bg:#FFFFFF; --bot-ink:#232B26;',
        '  --user-bg:#0F6E56; --user-ink:#F4F2EA;',
        '  --chip-bg:rgba(15,110,86,.06); --chip-ink:#0F6E56; --chip-line:rgba(15,110,86,.22);',
        '  --launch-bg:#072B22; --launch-ink:#F1EFE8;',
        '  --panel-shadow:0 32px 64px -28px rgba(7,43,34,.45), 0 8px 24px -12px rgba(7,43,34,.22);',
        '}',
        /* ---- dark skin (legacy dark pages) ---- */
        ':host(.dark){',
        '  --paper:#0A1310; --surface:#16261F; --ink:#EAE7DD; --muted:#9BA79E;',
        '  --line:rgba(241,239,232,.13); --field:#101D19;',
        '  --bot-bg:#1A2C25; --bot-ink:#EAE7DD;',
        '  --user-bg:#158268; --user-ink:#F1EFE8;',
        '  --chip-bg:rgba(21,130,104,.14); --chip-ink:#7FCDB4; --chip-line:rgba(127,205,180,.28);',
        '  --launch-bg:#0F6E56; --launch-ink:#F1EFE8;',
        '  --panel-shadow:0 32px 64px -24px rgba(0,0,0,.7), 0 0 0 1px rgba(241,239,232,.06);',
        '}',

        '*,*::before,*::after{box-sizing:border-box}',

        /* ---------- launcher ---------- */
        '.launch{',
        '  width:58px;height:58px;border-radius:50%;border:0;cursor:pointer;padding:0;',
        '  background:var(--launch-bg);color:var(--launch-ink);',
        '  display:flex;align-items:center;justify-content:center;position:relative;',
        '  box-shadow:0 18px 34px -14px rgba(7,43,34,.6);',
        '  transition:transform .28s var(--ease), box-shadow .28s var(--ease);',
        '}',
        '.launch:hover{transform:translateY(-3px);box-shadow:0 24px 42px -14px rgba(7,43,34,.7)}',
        '.launch:focus-visible{outline:3px solid var(--amber-bright);outline-offset:3px}',
        '.launch svg{width:27px;height:27px;display:block}',
        /* amber presence dot, doubling as the "we have history" marker */
        '.launch::after{',
        '  content:"";position:absolute;top:5px;inset-inline-end:5px;width:10px;height:10px;',
        '  border-radius:50%;background:#5FD1A4;box-shadow:0 0 0 3px var(--launch-bg);',
        '}',
        /* amber instead of green when there is a conversation waiting to resume */
        ':host(.has-history) .launch::after{background:var(--amber-bright)}',
        ':host(.open) .launch{transform:scale(.86);opacity:0;pointer-events:none}',
        

        /* ---------- panel ---------- */
        '.panel{',
        '  position:absolute;bottom:74px;width:min(384px, calc(100vw - 40px));',
        '  height:min(608px, calc(100vh - 128px));',
        '  background:var(--paper);color:var(--ink);',
        '  border-radius:20px;overflow:hidden;display:flex;flex-direction:column;',
        '  box-shadow:var(--panel-shadow);',
        '  opacity:0;visibility:hidden;transform:translateY(16px) scale(.97);',
        '  transition:opacity .24s var(--ease), transform .34s var(--ease), visibility .34s;',
        '}',
        ':host(.ltr) .panel{right:0;left:auto;transform-origin:100% 100%}',
        ':host(.rtl) .panel{left:0;right:auto;transform-origin:0 100%}',
        ':host(.open) .panel{opacity:1;visibility:visible;transform:translateY(0) scale(1)}',

        /* ---------- header ---------- */
        '.head{',
        '  padding:15px 16px;background:linear-gradient(135deg,var(--teal-900),var(--teal-950));',
        '  color:#F1EFE8;display:flex;align-items:center;gap:11px;flex:none;',
        '}',
        '.mark{',
        '  width:38px;height:38px;flex:none;border-radius:11px;display:flex;align-items:center;',
        '  justify-content:center;background:rgba(241,239,232,.09);',
        '  border:1px solid rgba(241,239,232,.18);color:#E8C98F;',
        '}',
        '.mark svg{width:21px;height:21px}',
        '.who{flex:1;min-width:0}',
        '.name{font-size:.98rem;font-weight:600;letter-spacing:.01em;display:flex;align-items:center;gap:7px}',
        '.dot{width:7px;height:7px;border-radius:50%;background:#5FD1A4;flex:none}',
        '.role{font-family:var(--mono);font-size:.63rem;letter-spacing:.13em;text-transform:uppercase;',
        '  color:rgba(241,239,232,.6);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
        '.x{',
        '  flex:none;width:32px;height:32px;border-radius:9px;border:0;cursor:pointer;padding:0;',
        '  background:rgba(241,239,232,.08);color:#F1EFE8;display:flex;align-items:center;justify-content:center;',
        '  transition:background .18s',
        '}',
        '.x:hover{background:rgba(241,239,232,.18)}',
        '.x:focus-visible{outline:2px solid var(--amber-bright);outline-offset:2px}',
        '.x svg{width:17px;height:17px}',

        /* ---------- context strip ---------- */
        '.ctx{',
        '  flex:none;display:flex;align-items:center;gap:8px;padding:9px 16px;',
        '  background:var(--surface);border-bottom:1px solid var(--line);',
        '  font-family:var(--mono);font-size:.64rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);',
        '}',
        '.ctx .label{color:var(--amber);flex:none}',
        ':host(.dark) .ctx .label{color:var(--amber-bright)}',
        '.ctx .where{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-transform:none;letter-spacing:.02em;font-size:.72rem;font-family:var(--sans)}',
        '.ctx .reset{',
        '  flex:none;background:none;border:0;padding:0;margin-inline-start:4px;cursor:pointer;color:var(--muted);',
        '  font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;text-decoration:underline;',
        '  text-underline-offset:3px',
        '}',
        '.ctx .reset:hover{color:var(--ink)}',

        /* ---------- body ---------- */
        '.body{flex:1 1 auto;overflow-y:auto;overscroll-behavior:contain;padding:16px;',
        '  display:flex;flex-direction:column;gap:11px;font-size:.9rem;scrollbar-width:thin}',
        '.body::-webkit-scrollbar{width:8px}',
        '.body::-webkit-scrollbar-thumb{background:var(--line);border-radius:8px}',

        '.msg{max-width:86%;padding:11px 14px;border-radius:16px;word-wrap:break-word;overflow-wrap:anywhere}',
        '.bot{background:var(--bot-bg);color:var(--bot-ink);border:1px solid var(--line);',
        '  border-end-start-radius:6px;margin-inline-end:auto}',
        '.user{background:var(--user-bg);color:var(--user-ink);border-end-end-radius:6px;margin-inline-start:auto}',
        '.msg strong{font-weight:600}',
        '.msg .li{display:block;padding-inline-start:14px;position:relative;margin:3px 0}',
        '.msg .li::before{content:"";position:absolute;inset-inline-start:2px;top:.62em;width:4px;height:4px;',
        '  border-radius:50%;background:currentColor;opacity:.55}',
        '.lnk{color:var(--user-bg);font-weight:500;text-decoration:underline;text-underline-offset:3px}',
        ':host(.dark) .lnk{color:#7FCDB4}',
        '.user .lnk{color:inherit}',
        '.faded{opacity:.62}',

        /* history divider */
        '.rule{display:flex;align-items:center;gap:10px;margin:2px 0;',
        '  font-family:var(--mono);font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}',
        '.rule::before,.rule::after{content:"";height:1px;background:var(--line);flex:1}',
        '.more{',
        '  align-self:center;background:none;border:1px solid var(--line);border-radius:99px;',
        '  padding:5px 13px;cursor:pointer;color:var(--muted);font-family:var(--mono);',
        '  font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;transition:border-color .18s,color .18s',
        '}',
        '.more:hover{border-color:var(--chip-line);color:var(--ink)}',

        /* suggestion + source chips */
        '.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:2px}',
        '.chip{',
        '  background:var(--chip-bg);color:var(--chip-ink);border:1px solid var(--chip-line);',
        '  border-radius:99px;padding:7px 13px;font-size:.79rem;font-family:inherit;cursor:pointer;',
        '  text-align:start;transition:background .18s,border-color .18s,transform .18s;',
        '  display:inline-flex;align-items:center;gap:6px;text-decoration:none;line-height:1.35',
        '}',
        '.chip:hover{background:var(--user-bg);border-color:var(--user-bg);color:var(--user-ink);transform:translateY(-1px)}',
        '.chip:focus-visible{outline:2px solid var(--amber-bright);outline-offset:2px}',
        '.chip .chevron{width:13px;height:13px;flex:none;opacity:.7}',
        ':host(.rtl) .chip .chevron{transform:scaleX(-1)}',
        '.chips-label{font-family:var(--mono);font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;',
        '  color:var(--muted);margin-bottom:-4px}',

        /* typing */
        '.typing{display:inline-flex;gap:4px;align-items:center;padding:14px}',
        '.typing i{width:6px;height:6px;border-radius:50%;background:var(--muted);display:block;',
        '  animation:bob 1.25s var(--ease) infinite}',
        '.typing i:nth-child(2){animation-delay:.16s}',
        '.typing i:nth-child(3){animation-delay:.32s}',
        '@keyframes bob{0%,60%,100%{opacity:.28;transform:translateY(0)}30%{opacity:1;transform:translateY(-4px)}}',
        '.err{background:rgba(166,67,31,.1);border-color:rgba(166,67,31,.35);color:#A6431F}',
        ':host(.dark) .err{color:#E9A88E}',

        /* ---------- composer ---------- */
        '.foot{flex:none;padding:12px 14px 14px;background:var(--surface);border-top:1px solid var(--line)}',
        '.field{display:flex;align-items:flex-end;gap:8px;background:var(--field);border:1px solid var(--line);',
        '  border-radius:14px;padding:6px 6px 6px 14px;transition:border-color .18s,box-shadow .18s}',
        ':host(.rtl) .field{padding:6px 14px 6px 6px}',
        '.field:focus-within{border-color:var(--user-bg);box-shadow:0 0 0 3px var(--chip-bg)}',
        'textarea{',
        '  flex:1;min-width:0;border:0;outline:0;background:transparent;resize:none;',
        '  font-family:inherit;font-size:.9rem;line-height:1.5;color:var(--ink);',
        '  padding:7px 0;max-height:110px;',
        '}',
        'textarea::placeholder{color:var(--muted);opacity:.85}',
        '.send{',
        '  flex:none;width:38px;height:38px;border-radius:11px;border:0;cursor:pointer;padding:0;',
        '  background:var(--user-bg);color:var(--user-ink);display:flex;align-items:center;justify-content:center;',
        '  transition:opacity .18s,transform .18s',
        '}',
        '.send svg{width:18px;height:18px}',
        ':host(.rtl) .send svg{transform:scaleX(-1)}',
        '.send:disabled{opacity:.32;cursor:default}',
        '.send:not(:disabled):hover{transform:translateY(-1px)}',
        '.send:focus-visible{outline:2px solid var(--amber-bright);outline-offset:2px}',
        '.legal{margin:8px 2px 0;font-family:var(--mono);font-size:.58rem;letter-spacing:.08em;',
        '  text-transform:uppercase;color:var(--muted);text-align:center}',

        /* ---------- phone: full-height sheet ---------- */
        '@media (max-width:520px){',
        '  .panel{position:fixed;inset-inline:0;bottom:0;width:100vw;height:88vh;height:88dvh;',
        '    border-radius:20px 20px 0 0;transform-origin:50% 100%}',
        '  :host(.ltr) .panel,:host(.rtl) .panel{inset-inline:0}',
        '}',
        /* Arabic pages: keep the sans face and drop the Latin tracking tricks */
        ':host(.ar) .role,:host(.ar) .ctx,:host(.ar) .ctx .reset,:host(.ar) .rule,',
        ':host(.ar) .chips-label,:host(.ar) .more,:host(.ar) .legal{',
        '  font-family:var(--sans);letter-spacing:0;text-transform:none}',
        ':host(.ar) .ctx,:host(.ar) .rule,:host(.ar) .chips-label,:host(.ar) .legal{font-size:.72rem}',
        ':host(.ar) .role{font-size:.72rem}',

        '@media (prefers-reduced-motion:reduce){',
        '  .panel,.launch,.chip,.send{transition-duration:.01ms}',
        '  .typing i{animation:none;opacity:.6}',
        '}'
    ].join('\n');

    // ---------- mount ----------

    var host = null;
    var shad = null;
    var els = {};
    var mounted = false;
    var initialized = false;
    var sending = false;
    var greeted = false;
    var thread = [];        // this page's live messages, appended to the transcript

    /**
     * Remove the widget markup that ten legacy pages still ship inline.
     * The launcher and the panel live in a shared fixed-position wrapper, so we
     * climb to that wrapper and drop the whole thing - removing only #aiden-ui
     * would leave the old blue launcher behind next to the new one.
     */
    function removeLegacyWidget() {
        var legacy = document.getElementById('aiden-ui');
        if (!legacy) return;
        var node = legacy;
        for (var hops = 0; hops < 3 && node.parentElement && node.parentElement !== document.body; hops++) {
            var parent = node.parentElement;
            if (getComputedStyle(parent).position === 'fixed') { node = parent; break; }
            node = parent;
        }
        if (node && node.parentNode) node.parentNode.removeChild(node);
    }

    /**
     * Stack above whatever else is pinned to this corner - the WhatsApp .fab on
     * the v4 pages and the blog hubs sits exactly where the launcher does.
     * Only body's first two levels are scanned; floating buttons are never
     * nested deeper than that, and scanning the whole document on a long
     * article would cost a layout pass for nothing.
     */
    function avoidCorner() {
        if (!host) return;
        var base = 20;
        var vh = window.innerHeight;
        var vw = window.innerWidth;
        var candidates = [];
        var top = document.body ? document.body.children : [];
        for (var i = 0; i < top.length && candidates.length < 300; i++) {
            candidates.push(top[i]);
            var kids = top[i].children;
            for (var j = 0; j < kids.length && candidates.length < 300; j++) candidates.push(kids[j]);
        }

        var needed = base;
        for (var k = 0; k < candidates.length; k++) {
            var el = candidates[k];
            if (el === host || el.tagName === 'SCRIPT' || el.tagName === 'STYLE') continue;
            var style = getComputedStyle(el);
            if (style.position !== 'fixed' || style.display === 'none' || style.visibility === 'hidden') continue;
            var r = el.getBoundingClientRect();
            if (!r.width || !r.height) continue;
            if (r.width > 340 || r.height > 170) continue;          // a bar, not a button
            if (r.bottom < vh - 220) continue;                      // not in the bottom band
            var nearSide = isRtl ? r.left < 180 : r.right > vw - 180;
            if (!nearSide) continue;
            needed = Math.max(needed, Math.round(vh - r.top) + 14);
        }
        host.style.setProperty('--bottom', Math.min(needed, 220) + 'px');
    }

    function el(tag, cls, html) {
        var node = document.createElement(tag);
        if (cls) node.className = cls;
        if (html !== undefined) node.innerHTML = html;
        return node;
    }

    function mount() {
        if (mounted || !document.body) return;
        // Shadow DOM is the whole isolation strategy. A browser without it is
        // ancient enough that the site is broken anyway; bail rather than mount
        // an unstyled widget into whichever CSS world the page happens to have.
        if (!document.body.attachShadow) return;
        removeLegacyWidget();

        host = document.createElement('div');
        host.id = 'aiden-root';
        host.className = isRtl ? 'rtl' : 'ltr';
        if (pageIsDark()) host.classList.add('dark');
        if (isAr) host.classList.add('ar');
        if (priorMessages.length) host.classList.add('has-history');

        shad = host.attachShadow({ mode: 'open' });

        var style = document.createElement('style');
        style.textContent = CSS;
        shad.appendChild(style);

        var wrap = el('div', 'wrap');
        wrap.innerHTML =
            '<div class="panel" role="dialog" aria-modal="false" aria-label="' +
            escapeHtml(t('Chat with Aiden', 'محادثة مع أيدن')) + '">' +
              '<div class="head">' +
                '<span class="mark">' + ICON_MARK + '</span>' +
                '<span class="who">' +
                  '<span class="name"><span>Aiden</span><span class="dot" aria-hidden="true"></span></span>' +
                  '<span class="role">' + escapeHtml(t('AI consultant · AI Profit Lab', 'مستشار الذكاء الاصطناعي · AI Profit Lab')) + '</span>' +
                '</span>' +
                '<button class="x" type="button" aria-label="' + escapeHtml(t('Close chat', 'إغلاق المحادثة')) + '">' + ICON_CLOSE + '</button>' +
              '</div>' +
              '<div class="ctx">' +
                '<span class="label"></span>' +
                '<span class="where"></span>' +
                '<button class="reset" type="button" hidden>' + escapeHtml(t('New chat', 'محادثة جديدة')) + '</button>' +
              '</div>' +
              '<div class="body" id="chat-messages" role="log" aria-live="polite" aria-relevant="additions"></div>' +
              '<div class="foot">' +
                '<div class="field">' +
                  '<textarea id="user-input" rows="1" placeholder="' +
                    escapeHtml(t('Ask Aiden anything…', 'اسأل أيدن عن أي شيء…')) + '" aria-label="' +
                    escapeHtml(t('Your message', 'رسالتك')) + '"></textarea>' +
                  '<button class="send" type="button" disabled aria-label="' +
                    escapeHtml(t('Send message', 'إرسال الرسالة')) + '">' + ICON_SEND + '</button>' +
                '</div>' +
                '<p class="legal">' + escapeHtml(t('Replies are AI-generated', 'الردود مولّدة بالذكاء الاصطناعي')) + '</p>' +
              '</div>' +
            '</div>' +
            '<button class="launch" type="button" aria-expanded="false" aria-label="' +
              escapeHtml(t('Open chat with Aiden', 'افتح المحادثة مع أيدن')) + '">' + ICON_MARK + '</button>';

        shad.appendChild(wrap);
        document.body.appendChild(host);

        els = {
            wrap: wrap,
            panel: wrap.querySelector('.panel'),
            body: wrap.querySelector('.body'),
            launch: wrap.querySelector('.launch'),
            close: wrap.querySelector('.x'),
            send: wrap.querySelector('.send'),
            input: wrap.querySelector('textarea'),
            ctxLabel: wrap.querySelector('.ctx .label'),
            ctxWhere: wrap.querySelector('.ctx .where'),
            reset: wrap.querySelector('.ctx .reset')
        };

        els.launch.addEventListener('click', function () { api.toggle(); });
        els.close.addEventListener('click', function () { api.close(); });
        els.send.addEventListener('click', function () { api.send(); });

        els.input.addEventListener('input', function () {
            els.send.disabled = !els.input.value.trim();
            els.input.style.height = 'auto';
            els.input.style.height = Math.min(els.input.scrollHeight, 110) + 'px';
        });
        els.input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); api.send(); }
        });
        els.reset.addEventListener('click', function () {
            clearTranscript();
            host.classList.remove('has-history');
            thread = [];
            greeted = false;
            els.body.innerHTML = '';
            els.reset.hidden = true;
            greet();
        });

        host.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && host.classList.contains('open')) { e.stopPropagation(); api.close(); }
        });

        renderContextStrip();
        avoidCorner();

        var resizeTimer;
        window.addEventListener('resize', function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(avoidCorner, 200);
        }, { passive: true });

        mounted = true;
    }

    function renderContextStrip() {
        var type = pageType(location.pathname);
        var labels = {
            article: t('Reading', 'تقرأ'), guide: t('Reading', 'تقرأ'),
            services: t('Viewing', 'تتصفح'), process: t('Viewing', 'تتصفح'),
            tool: t('Using', 'تستخدم'), demo: t('Viewing', 'تتصفح')
        };
        els.ctxLabel.textContent = labels[type] || t('Viewing', 'تتصفح');
        els.ctxWhere.textContent = pageTitle().slice(0, 80);
    }

    // ---------- message rendering ----------

    function scrollToEnd() {
        if (!els.body) return;
        requestAnimationFrame(function () { els.body.scrollTop = els.body.scrollHeight; });
    }

    function bubble(html, who, extraClass) {
        var node = el('div', 'msg ' + who + (extraClass ? ' ' + extraClass : ''), html);
        els.body.appendChild(node);
        scrollToEnd();
        return node;
    }

    function divider(text) {
        els.body.appendChild(el('div', 'rule', escapeHtml(text)));
    }

    /** Clickable prompts. Selecting one sends it as if the visitor typed it. */
    function renderSuggestions(list) {
        if (!list || !list.length) return;
        var box = el('div', 'chips');
        list.forEach(function (text) {
            var chip = el('button', 'chip', escapeHtml(text));
            chip.type = 'button';
            chip.addEventListener('click', function () {
                box.remove();
                api.send(text);
            });
            box.appendChild(chip);
        });
        els.body.appendChild(box);
        scrollToEnd();
    }

    /** Pages the backend judged relevant - the "guide me somewhere else" rail. */
    function renderSources(sources) {
        if (!sources || !sources.length) return;
        var links = sources.filter(function (s) { return s && safeUrl(s.url); });
        if (!links.length) return;

        els.body.appendChild(el('div', 'chips-label', escapeHtml(t('Explore next', 'تابع من هنا'))));
        var box = el('div', 'chips');
        links.slice(0, 3).forEach(function (s) {
            var a = el('a', 'chip', escapeHtml(String(s.title || '').slice(0, 64)) + ICON_ARROW);
            a.href = safeUrl(s.url);
            box.appendChild(a);
        });
        els.body.appendChild(box);
        scrollToEnd();
    }

    // ---------- greeting, including the returning visitor ----------

    function replayPriorConversation() {
        if (!priorMessages.length) return;

        var recent = priorMessages.slice(-4);
        var hidden = priorMessages.slice(0, -4);

        divider(t('Earlier · ' + relativeWhen(priorContext.updatedAt),
            'سابقاً · ' + relativeWhen(priorContext.updatedAt)));

        if (hidden.length) {
            var more = el('button', 'more', escapeHtml(
                t('Show ' + hidden.length + ' earlier messages', 'عرض ' + hidden.length + ' رسالة سابقة')));
            more.type = 'button';
            more.addEventListener('click', function () {
                var anchor = more.nextSibling;
                hidden.forEach(function (m) {
                    var node = el('div', 'msg ' + (m.role === 'user' ? 'user' : 'bot') + ' faded',
                        m.role === 'user' ? escapeHtml(m.text) : renderMarkdown(m.text));
                    els.body.insertBefore(node, anchor);
                });
                more.remove();
            });
            els.body.appendChild(more);
        }

        recent.forEach(function (m) {
            bubble(m.role === 'user' ? escapeHtml(m.text) : renderMarkdown(m.text),
                m.role === 'user' ? 'user' : 'bot', 'faded');
        });

        divider(t('Today', 'اليوم'));
    }

    function welcomeBack() {
        var topic = lastTopic();
        var when = relativeWhen(priorContext.updatedAt);
        var samePage = priorContext.page === location.pathname;

        var line;
        if (topic && topic.length > 4) {
            var short = topic.length > 90 ? topic.slice(0, 90).replace(/\s+\S*$/, '') + '…' : topic;
            line = t('Welcome back. ' + when.charAt(0).toUpperCase() + when.slice(1) +
                     ' you asked about "' + short + '" — want to carry on from there, or is today something else?',
                     'أهلاً بعودتك. ' + when + ' سألت عن "' + short +
                     '" — تحب أن نكمل من هناك، أم لديك موضوع آخر اليوم؟');
        } else {
            line = t('Welcome back — good to see you again. What can I help with today?',
                     'أهلاً بعودتك — سعيد برؤيتك مجدداً. كيف أساعدك اليوم؟');
        }
        // Only name the page they were on when there is no topic to name -
        // saying both makes the greeting read like a surveillance report.
        if (!topic && !samePage && priorContext.pageTitle) {
            line += ' ' + t('You were reading "' + priorContext.pageTitle.slice(0, 60) + '" last time.',
                            'كنت تقرأ "' + priorContext.pageTitle.slice(0, 60) + '" في المرة الماضية.');
        }
        bubble(escapeHtml(line), 'bot');
    }

    function greet() {
        if (greeted) return;
        greeted = true;

        var type = pageType(location.pathname);

        if (priorMessages.length && priorContext) {
            replayPriorConversation();
            welcomeBack();
            els.reset.hidden = false;
            renderSuggestions([
                t('Pick up where we left off', 'أكمل من حيث توقفنا')
            ].concat(suggestionsFor(type).slice(0, 2)));
            return;
        }

        if (priorVisit.count > 1) {
            bubble(escapeHtml(t('Good to see you back. ', 'سعيد بعودتك. ') +
                pageGreeting(type, true)), 'bot');
        } else {
            bubble(escapeHtml(pageGreeting(type, false)), 'bot');
        }
        renderSuggestions(suggestionsFor(type));
    }

    // ---------- talking to the backend ----------

    /**
     * The request body. `history` is the conversation BEFORE this message: the
     * message itself travels in `message`, and including it in both would put
     * it in front of the model twice.
     */
    function payload(message) {
        var signals = behaviour();
        var history = priorMessages.concat(thread).slice(-HISTORY_TO_SEND).map(function (m) {
            return { role: m.role === 'user' ? 'user' : 'assistant', content: String(m.text).slice(0, 1200) };
        });

        return {
            message: message,
            sessionId: visitorId(),
            email: lsGet(K_EMAIL, ''),
            language: isAr ? 'ar' : 'en',
            country: lsGet('visitorCountry', ''),
            countryCode: lsGet('visitorCountryCode', ''),

            // what the visitor is looking at right now
            page: location.pathname,
            pageTitle: pageTitle(),
            pageType: pageType(location.pathname),
            pageDescription: pageDescription(),
            pageHeadings: pageHeadings(),
            journey: trackJourney(),

            // how engaged they are with it
            secondsOnPage: signals.secondsOnPage,
            scrollDepth: signals.scrollDepth,
            referrer: signals.referrer,

            // who they are across visits
            visitCount: priorVisit.count,
            isReturning: priorVisit.count > 1,
            firstVisit: lsGet(K_FIRST, ''),
            daysSinceLastVisit: priorVisit.days,
            previousPages: pagesBeforeThisOne.slice(-8),

            // the conversation they can see in front of them
            history: history,
            hasPriorConversation: priorMessages.length > 0
        };
    }

    /**
     * Rough location, used only as context for the backend ("Location: Oman").
     * Deferred to the first time the panel opens - an article view should not
     * pay for a third-party lookup nobody reads - and cached for 30 days so a
     * regular visitor costs one request, not one per session.
     */
    var countryRequested = false;

    function detectCountry() {
        if (countryRequested) return;
        countryRequested = true;

        var cachedAt = parseInt(lsGet('visitorCountryAt', '0'), 10) || 0;
        if (lsGet('visitorCountry', '') && Date.now() - cachedAt < 30 * 86400000) return;

        fetch('https://ipapi.co/json/')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!data || !data.country_name) return;
                lsSet('visitorCountry', String(data.country_name).slice(0, 60));
                lsSet('visitorCountryCode', String(data.country_code || '').slice(0, 4));
                lsSet('visitorCountryAt', String(Date.now()));
            })
            .catch(function () { /* location is optional context, never a blocker */ });
    }

    function track(event, params) {
        try { if (typeof window.gtag === 'function') window.gtag('event', event, params || {}); } catch (e) { /* ok */ }
    }

    // ---------- public API ----------

    var api = {
        init: function () {
            if (initialized) return;
            initialized = true;

            visitorId();
            priorVisit = openVisit();
            trackJourney();
            trackPagesSeen();
            mount();

            window.addEventListener('scroll', trackScroll, { passive: true });
        },

        open: function () {
            if (!mounted) api.init();
            if (!host || host.classList.contains('open')) return;
            host.classList.add('open');
            els.launch.setAttribute('aria-expanded', 'true');
            detectCountry();
            greet();
            track('aiden_open', { page_path: location.pathname, returning: priorVisit.count > 1 });
            setTimeout(function () { if (window.innerWidth > 520) els.input.focus(); }, 260);
        },

        close: function () {
            if (!host) return;
            host.classList.remove('open');
            els.launch.setAttribute('aria-expanded', 'false');
            els.launch.focus();
        },

        toggle: function () {
            if (!mounted) api.init();
            if (host && host.classList.contains('open')) api.close(); else api.open();
        },

        send: async function (preset) {
            if (!mounted) api.init();
            if (sending) return;

            var msg = String(preset !== undefined && preset !== null ? preset : els.input.value).trim();
            if (!msg) return;
            msg = msg.slice(0, MAX_MSG_CHARS);

            if (preset === undefined || preset === null) {
                els.input.value = '';
                els.input.style.height = 'auto';
            }
            els.send.disabled = true;
            sending = true;

            bubble(escapeHtml(msg), 'user');
            // Built before the message joins the thread, so it carries the
            // conversation up to this point and not the message itself.
            var body = payload(msg);
            thread.push({ role: 'user', text: msg });
            saveTranscript(priorMessages.concat(thread));
            track('aiden_message', { page_path: location.pathname });

            var typing = bubble('<span class="typing"><i></i><i></i><i></i></span>', 'bot');

            var controller = typeof AbortController === 'function' ? new AbortController() : null;
            var timer = controller ? setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS) : null;

            try {
                var res = await fetch(API, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                    signal: controller ? controller.signal : undefined
                });
                // Load-bearing. A dead backend answers every path with its
                // own 404 page, and that page is valid JSON - so res.json()
                // resolves, no field matches, and the widget used to fall
                // through to the filler line below and answer every message
                // with it, forever, without ever erroring. Saying we are
                // unavailable costs far less than answering nothing
                // convincingly, so anything but a 2xx goes to the catch.
                if (!res.ok) throw new Error('HTTP ' + res.status);
                var result = await res.json();
                var reply = result.reply || result.response;
                if (!reply) throw new Error('no reply field');
                typing.remove();

                bubble(renderMarkdown(reply), 'bot');
                thread.push({ role: 'assistant', text: reply });
                saveTranscript(priorMessages.concat(thread));
                renderSources(result.sources);
            } catch (e) {
                typing.remove();
                // Hand the visitor somewhere that works, as a real link -
                // this is the only path left when the backend is down.
                bubble(escapeHtml(t('I could not reach the server just then. Try again in a moment — or message us on WhatsApp: ',
                    'تعذّر الوصول إلى الخادم الآن. حاول مرة أخرى بعد قليل — أو راسلنا على واتساب: ')) +
                    '<a href="' + WHATSAPP_URL + '" target="_blank" rel="noopener">' +
                    escapeHtml(t('Chat on WhatsApp', 'المحادثة على واتساب')) + '</a>', 'bot', 'err');
            } finally {
                if (timer) clearTimeout(timer);
                sending = false;
                els.send.disabled = !els.input.value.trim();
                scrollToEnd();
            }
        }
    };

    window.aidenChat = api;

    // Self-start. Held until after load so the widget never competes with page
    // rendering; pages that lazy-load this file and call init() themselves are
    // unaffected, because init() is guarded.
    function boot() { api.init(); }

    if (document.readyState === 'complete') {
        setTimeout(boot, 0);
    } else {
        window.addEventListener('load', function () { setTimeout(boot, 900); });
    }
})();
