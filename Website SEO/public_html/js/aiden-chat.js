// ==================== AIDEN CHATBOT WIDGET CONTROLLER ====================
//
// Public API is unchanged (init / toggle / send) so every page that already
// lazy-loads this file keeps working without edits.
//
// What it sends to the backend: the page the visitor is on, the trail of pages
// they visited this session, and how engaged they are with the current page.
// The backend uses that to answer in context and to link to relevant pages.

(function () {
    'use strict';

    var API = 'https://aiden-backend-aiden.up.railway.app/chat';
    var SITE_HOST = 'aiprofitlab.io';

    // ---------- visitor identity & journey ----------

    function visitorId() {
        var id = localStorage.getItem('aidenVisitorId');
        if (!id) {
            id = 'visitor_' + Date.now() + '_' + Math.random().toString(36).slice(2, 11);
            localStorage.setItem('aidenVisitorId', id);
            localStorage.setItem('aidenVisitCount', '1');
            localStorage.setItem('aidenFirstVisit', new Date().toISOString());
        }
        return id;
    }

    function pageTitle() {
        var h1 = document.querySelector('h1');
        return (h1 && h1.textContent.trim()) || document.title || '';
    }

    // Trail of pages viewed in this browser tab session.
    function trackJourney() {
        var trail = [];
        try {
            trail = JSON.parse(sessionStorage.getItem('aidenJourney') || '[]');
        } catch (e) {
            trail = [];
        }
        var here = location.pathname;
        if (!trail.length || trail[trail.length - 1].path !== here) {
            trail.push({ path: here, title: pageTitle().slice(0, 120) });
            if (trail.length > 20) trail.shift();
            try {
                sessionStorage.setItem('aidenJourney', JSON.stringify(trail));
            } catch (e) { /* private mode: journey is best-effort */ }
        }
        return trail;
    }

    // How engaged is the visitor with this page right now?
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

    // ---------- safe rendering ----------

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Only same-site links are ever rendered as anchors. Anything else stays
    // as plain text, so a malformed or injected URL can't become javascript:.
    function safeUrl(url) {
        if (/^\/(?!\/)/.test(url)) return url;                       // /path
        if (/^https?:\/\/([\w-]+\.)?aiprofitlab\.io(\/|$)/i.test(url)) return url;
        return null;
    }

    // Minimal markdown: links, bold, line breaks. Input is escaped first, so no
    // raw HTML from the model can reach the DOM.
    function renderMarkdown(text) {
        var html = escapeHtml(text);

        html = html.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, function (match, label, url) {
            var href = safeUrl(url);
            if (!href) return label;
            return '<a href="' + href + '" class="aiden-link text-blue-400 underline hover:text-blue-300">' + label + '</a>';
        });

        html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\n{2,}/g, '<br><br>').replace(/\n/g, '<br>');
        return html;
    }

    // ---------- DOM helpers ----------

    function messagesBox() {
        return document.getElementById('chat-messages');
    }

    function scrollToEnd() {
        var box = messagesBox();
        if (box) requestAnimationFrame(function () { box.scrollTop = box.scrollHeight; });
    }

    function appendBubble(html, cls, alignEnd) {
        var box = messagesBox();
        if (!box) return null;
        var el = document.createElement('div');
        el.className = cls;
        // Logical alignment so the layout mirrors correctly on the Arabic (RTL) pages.
        if (alignEnd) el.style.marginInlineStart = 'auto';
        el.innerHTML = html;
        box.appendChild(el);
        scrollToEnd();
        return el;
    }

    var BOT_CLS = 'aiden-bubble aiden-bubble-bot bg-gray-800 p-3 rounded-2xl max-w-[85%] text-gray-300 leading-relaxed';
    var USER_CLS = 'aiden-bubble aiden-bubble-user bg-blue-900/50 p-3 rounded-2xl max-w-[85%] text-white';

    function renderSources(sources) {
        if (!sources || !sources.length) return;
        var isEn = document.documentElement.lang === 'en';
        var links = sources.map(function (s) {
            var href = safeUrl(s.url);
            if (!href) return '';
            return '<a href="' + href + '" class="aiden-chip inline-block bg-gray-900 border border-gray-700 hover:border-blue-500 ' +
                'rounded-full px-3 py-1 text-[11px] text-gray-300 hover:text-blue-300 transition mr-1 mb-1">' +
                escapeHtml(s.title.slice(0, 60)) + '</a>';
        }).filter(Boolean).join('');
        if (!links) return;
        appendBubble(
            '<span class="aiden-sources-label block text-[10px] uppercase tracking-wider text-gray-500 mb-1">' +
            (isEn ? 'Related on our site' : 'ذات صلة على موقعنا') + '</span>' + links,
            'aiden-sources max-w-[95%]'
        );
    }

    // ---------- greeting ----------

    function pageGreeting() {
        var path = location.pathname;
        var isEn = document.documentElement.lang === 'en';

        if (/services|packages/.test(path)) {
            return isEn
                ? 'Which package seems right for your business? I can explain the details.'
                : 'أي باقة تبدو مناسبة لعملك؟ يمكنني شرح التفاصيل.';
        }
        if (/process/.test(path)) {
            return isEn
                ? 'Our process is simple: Discover, Build, Support. Which step would you like to understand better?'
                : 'طريقتنا بسيطة: نكتشف، نبني، ندعم. أي خطوة تود فهمها أكثر؟';
        }
        if (/contact/.test(path)) {
            return isEn
                ? 'You can contact us directly, or write your question now.'
                : 'يمكنك التواصل معنا مباشرة، أو اكتب سؤالك الآن.';
        }
        if (/about/.test(path)) {
            return isEn
                ? 'We build smart systems for GCC businesses. What would you like to know about us?'
                : 'نبني أنظمة ذكية للشركات العمانية. ماذا تريد أن تعرف عنا؟';
        }
        if (/\/blog\/|\/academy\//.test(path)) {
            var topic = pageTitle().slice(0, 70);
            return isEn
                ? 'Reading about "' + topic + '"? Ask me anything about it, or how it would work for your business.'
                : 'تقرأ عن "' + topic + '"؟ اسألني أي شيء عنه، أو كيف يمكن تطبيقه في عملك.';
        }
        if (/simulator|calculator/.test(path)) {
            return isEn
                ? 'Want help reading these numbers? Tell me about your business and I will walk you through them.'
                : 'تريد مساعدة في فهم هذه الأرقام؟ أخبرني عن عملك وسأشرحها لك.';
        }
        if (/demo/.test(path)) {
            return isEn
                ? 'Curious how this demo would work for your business? Ask away.'
                : 'تريد معرفة كيف يعمل هذا العرض في مجال عملك؟ اسألني.';
        }
        if (/offer/.test(path)) {
            return isEn
                ? 'Questions about this offer? I can explain exactly what is included.'
                : 'لديك أسئلة حول هذا العرض؟ يمكنني شرح ما يتضمنه بالتفصيل.';
        }
        return isEn ? 'Hello! How can I help you today?' : 'مرحباً! كيف يمكنني مساعدتك اليوم؟';
    }

    // ---------- self-mounting ----------
    //
    // Ten pages ship the widget markup inline. Everywhere else (articles,
    // guides, demos, tools) this script builds the same DOM itself, so a single
    // <script src="/js/aiden-chat.js"> is all a page needs.

    var selfMounted = false;

    // The self-mounted markup above carries Tailwind utility classes, which only
    // resolve on pages that load the Tailwind CDN. The v4 pages and the storefront
    // pages ship self-contained CSS and no Tailwind, so the widget would mount
    // unstyled there. These rules restate the same values scoped under #aiden-root:
    // an id+class selector outranks a bare utility class, so pages that DO load
    // Tailwind render exactly as before, and pages that don't now render correctly.
    var SKIN_CSS =
        '#aiden-root,#aiden-root *,#aiden-root *::before,#aiden-root *::after{box-sizing:border-box}' +
        '#aiden-root{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,' +
        '"Helvetica Neue",Arial,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased}' +
        '#aiden-root #aiden-launcher{background-color:#2563eb;border-radius:9999px;display:flex;' +
        'align-items:center;justify-content:center;padding:0;' +
        'box-shadow:0 25px 50px -12px rgba(0,0,0,.25);transition:background-color .15s cubic-bezier(.4,0,.2,1)}' +
        '#aiden-root #aiden-launcher:hover{background-color:#3b82f6}' +
        '#aiden-root #aiden-launcher svg{width:1.75rem;height:1.75rem;color:#fff;display:block}' +
        '#aiden-root #aiden-ui{background-color:#0f0f0f;border:1px solid #1f2937;border-radius:1.5rem;' +
        'box-shadow:0 25px 50px -12px rgba(0,0,0,.25);display:flex;flex-direction:column;overflow:hidden}' +
        '#aiden-root .aiden-head{padding:1rem;background-image:linear-gradient(to right,#1e3a8a,#000);' +
        'display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1f2937}' +
        '#aiden-root .aiden-brand{font-weight:700;font-size:.875rem;letter-spacing:.1em;color:#fff}' +
        '#aiden-root .aiden-a{color:#3b82f6}#aiden-root .aiden-i{color:#ef4444}' +
        '#aiden-root .aiden-dot{color:#4ade80;font-size:10px;margin-inline-start:.5rem}' +
        '#aiden-root .aiden-country{font-size:.75rem;color:#9ca3af}' +
        '#aiden-root #aiden-close{color:#fff;opacity:.5;font-weight:700;font-size:1.25rem;line-height:1;' +
        'background:transparent;border:0;cursor:pointer;padding:0;font-family:inherit}' +
        '#aiden-root #aiden-close:hover{opacity:1}' +
        '#aiden-root .aiden-body{flex:1 1 0%;padding:1.25rem;overflow-y:auto;font-size:.875rem;color:#d1d5db}' +
        '#aiden-root .aiden-body > * + *{margin-top:1rem}' +
        '#aiden-root .aiden-bubble{padding:.75rem;border-radius:1rem;max-width:85%;line-height:1.625}' +
        '#aiden-root .aiden-bubble-bot{background-color:#1f2937;color:#d1d5db}' +
        '#aiden-root .aiden-bubble-user{background-color:rgba(30,58,138,.5);color:#fff}' +
        '#aiden-root .aiden-sub{display:block;font-size:.75rem;color:#9ca3af;margin-top:.25rem}' +
        '#aiden-root .aiden-link{color:#60a5fa;text-decoration:underline}' +
        '#aiden-root .aiden-link:hover{color:#93c5fd}' +
        '#aiden-root .aiden-sources{max-width:95%}' +
        '#aiden-root .aiden-sources-label{display:block;font-size:10px;text-transform:uppercase;' +
        'letter-spacing:.05em;color:#6b7280;margin-bottom:.25rem}' +
        '#aiden-root .aiden-chip{display:inline-block;background-color:#111827;border:1px solid #374151;' +
        'border-radius:9999px;padding:.25rem .75rem;font-size:11px;color:#d1d5db;text-decoration:none;' +
        'margin-inline-end:.25rem;margin-bottom:.25rem;transition:border-color .15s,color .15s}' +
        '#aiden-root .aiden-chip:hover{border-color:#3b82f6;color:#93c5fd}' +
        '#aiden-root .aiden-foot{padding:.75rem;background-color:#050505;border-top:1px solid #1f2937;' +
        'display:flex;align-items:center}' +
        '#aiden-root #user-input{flex:1 1 0%;min-width:0;background:transparent;border:0;outline:none;' +
        'font-size:.875rem;color:#fff;padding:.5rem 0;font-family:inherit}' +
        '#aiden-root #user-input::placeholder{color:#6b7280}' +
        '#aiden-root #aiden-send{background-color:#2563eb;color:#fff;padding:.25rem 1rem;border-radius:9999px;' +
        'font-size:.75rem;font-weight:700;border:0;cursor:pointer;white-space:nowrap;font-family:inherit;' +
        'margin-inline-start:.5rem;transition:background-color .15s}' +
        '#aiden-root #aiden-send:hover{background-color:#3b82f6}' +
        '#aiden-root .aiden-typing{display:inline-block;animation:aiden-pulse 2s cubic-bezier(.4,0,.6,1) infinite}' +
        '@keyframes aiden-pulse{0%,100%{opacity:1}50%{opacity:.5}}';


    function widgetStyles() {
        if (document.getElementById('aiden-injected-style')) return;
        var css = document.createElement('style');
        css.id = 'aiden-injected-style';
        css.textContent =
            '#aiden-root{position:fixed;bottom:20px;z-index:10005}' +
            'html[dir="rtl"] #aiden-root{left:20px;right:auto}' +
            'html:not([dir="rtl"]) #aiden-root{right:20px;left:auto}' +
            '#aiden-ui{position:absolute;bottom:80px;width:350px;height:500px;' +
            'transform:translateY(120%);visibility:hidden;opacity:0;' +
            'transition:transform .5s cubic-bezier(.16,1,.3,1),opacity .3s,visibility .3s}' +
            'html[dir="rtl"] #aiden-ui{left:0;right:auto}' +
            'html:not([dir="rtl"]) #aiden-ui{right:0;left:auto}' +
            '#aiden-ui.active{transform:translateY(0);visibility:visible;opacity:1}' +
            '@media(max-width:420px){#aiden-ui{width:calc(100vw - 40px)}}' +
            '#aiden-launcher{width:60px;height:60px;border:0;cursor:pointer}' + SKIN_CSS;
        document.head.appendChild(css);
    }

    function mountWidget() {
        if (document.getElementById('aiden-ui')) return false; // page ships its own
        if (!document.body) return false;

        widgetStyles();
        var isEn = document.documentElement.lang !== 'ar';

        var root = document.createElement('div');
        root.id = 'aiden-root';
        root.innerHTML =
            '<button id="aiden-launcher" aria-label="' +
            (isEn ? 'Open chat with Aiden' : 'افتح المحادثة مع أيدن') +
            '" class="bg-blue-600 hover:bg-blue-500 rounded-full flex items-center justify-center shadow-2xl transition">' +
            '<svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" width="28" height="28">' +
            '<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" ' +
            'stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg></button>' +

            '<div id="aiden-ui" class="bg-[#0f0f0f] border border-gray-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden">' +
            '<div class="aiden-head p-4 bg-gradient-to-r from-blue-900 to-black flex justify-between items-center border-b border-gray-800">' +
            '<span class="aiden-brand font-bold text-sm tracking-widest text-white">' +
            '<span class="aiden-a text-blue-500">A</span><span class="aiden-i text-red-500">I</span>DEN' +
            '<span class="aiden-dot text-green-400 text-[10px] ml-2">● ONLINE</span></span>' +
            '<span class="aiden-country text-xs text-gray-400" id="visitor-country"></span>' +
            '<button id="aiden-close" aria-label="' + (isEn ? 'Close chat' : 'إغلاق المحادثة') +
            '" class="text-white opacity-50 hover:opacity-100 font-bold text-xl bg-transparent border-0 cursor-pointer">✕</button></div>' +
            '<div class="aiden-body flex-1 p-5 overflow-y-auto space-y-4 text-sm text-gray-300" id="chat-messages">' +
            '<div class="aiden-bubble aiden-bubble-bot bg-gray-800 p-4 rounded-2xl max-w-[85%]"><span class="aiden-sub block text-xs text-gray-400 mt-1" id="welcome-message"></span></div></div>' +
            '<div class="aiden-foot p-3 bg-[#050505] border-t border-gray-800 flex items-center">' +
            '<input class="bg-transparent border-none outline-none flex-1 text-sm text-white py-2" id="user-input" ' +
            'placeholder="' + (isEn ? 'Type your message...' : 'اكتب رسالتك...') + '" type="text">' +
            '<button id="aiden-send" class="bg-blue-600 text-white px-4 py-1 rounded-full text-xs font-bold hover:bg-blue-500 transition ml-2 border-0 cursor-pointer">' +
            (isEn ? 'SEND' : 'إرسال') + '</button></div></div>';

        document.body.appendChild(root);

        root.querySelector('#aiden-launcher').addEventListener('click', function () { window.aidenChat.toggle(); });
        root.querySelector('#aiden-close').addEventListener('click', function () { window.aidenChat.toggle(); });
        root.querySelector('#aiden-send').addEventListener('click', function () { window.aidenChat.send(); });

        selfMounted = true;
        return true;
    }

    // ---------- country ----------

    async function detectCountry() {
        try {
            var res = await fetch('https://ipapi.co/json/');
            var data = await res.json();
            var isEn = document.documentElement.lang === 'en';
            var country = data.country_name || (isEn ? 'Oman' : 'عمان');
            var code = data.country_code || 'OM';
            localStorage.setItem('visitorCountry', country);
            localStorage.setItem('visitorCountryCode', code);

            var span = document.getElementById('visitor-country');
            if (span) span.textContent = code;
            var welcome = document.getElementById('welcome-message');
            if (welcome) {
                welcome.textContent = isEn ? 'Welcome from ' + country + '!' : 'مرحباً بك من ' + country + '!';
            }
        } catch (e) {
            /* country detection is optional */
        }
    }

    // ---------- public API ----------

    var sending = false;
    var countryRequested = false;

    var initialized = false;

    window.aidenChat = {
        init: function () {
            if (initialized) return;   // pages with inline markup call this themselves
            initialized = true;

            visitorId();
            trackJourney();
            mountWidget();

            window.addEventListener('scroll', trackScroll, { passive: true });

            var input = document.getElementById('user-input');
            if (input && !input.dataset.aidenBound) {
                input.dataset.aidenBound = '1';
                input.addEventListener('keydown', function (e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        window.aidenChat.send();
                    }
                });
            }
        },

        toggle: function () {
            var chat = document.getElementById('aiden-ui');
            if (!chat) return;
            chat.classList.toggle('active');
            if (!chat.classList.contains('active')) return;

            // Deferred to first open so article pages don't pay a geo lookup
            // on every view just to render a greeting nobody sees.
            if (!countryRequested) {
                countryRequested = true;
                detectCountry();
            }

            var box = messagesBox();
            var welcome = document.getElementById('welcome-message');
            var welcomeText = (welcome && welcome.textContent) || '';
            if (box && box.children.length <= 1) {
                box.innerHTML =
                    '<div class="' + BOT_CLS + '">' + escapeHtml(pageGreeting()) +
                    '<span class="aiden-sub block text-xs text-gray-500 mt-1">' + escapeHtml(welcomeText) + '</span></div>';
            }
            var input = document.getElementById('user-input');
            if (input) input.focus();
        },

        send: async function () {
            if (sending) return;

            var input = document.getElementById('user-input');
            var box = messagesBox();
            if (!input || !box) return;

            var msg = input.value.trim();
            if (!msg) return;

            var isEn = document.documentElement.lang === 'en';
            var vid = visitorId();
            var visitCount = parseInt(localStorage.getItem('aidenVisitCount') || '1', 10);

            sending = true;
            input.value = '';

            appendBubble(escapeHtml(msg), USER_CLS, true);
            var typing = appendBubble(
                '<span class="aiden-typing inline-block animate-pulse">●●●</span>',
                'aiden-bubble aiden-bubble-bot bg-gray-800 p-3 rounded-2xl max-w-[85%] text-gray-500'
            );

            try {
                var signals = behaviour();
                var res = await fetch(API, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: msg,
                        sessionId: vid,
                        email: localStorage.getItem('aidenVisitorEmail') || '',
                        language: isEn ? 'en' : 'ar',
                        country: localStorage.getItem('visitorCountry') || (isEn ? 'Oman' : 'عمان'),
                        countryCode: localStorage.getItem('visitorCountryCode') || 'OM',

                        // page awareness
                        page: location.pathname,
                        pageTitle: pageTitle(),
                        journey: trackJourney(),

                        // behavioural signals
                        secondsOnPage: signals.secondsOnPage,
                        scrollDepth: signals.scrollDepth,
                        referrer: signals.referrer,

                        visitCount: visitCount,
                        isReturning: visitCount > 1,
                        firstVisit: localStorage.getItem('aidenFirstVisit')
                    })
                });

                var result = await res.json();
                if (typing) typing.remove();

                var reply = result.reply || result.response ||
                    (isEn ? 'Thank you for your message!' : 'شكراً لرسالتك! دعنا نكمل.');

                appendBubble(renderMarkdown(reply), BOT_CLS);
                renderSources(result.sources);
            } catch (e) {
                if (typing) typing.remove();
                appendBubble(
                    isEn ? 'Connection error. Please try again.' : 'عذراً، حدث خطأ. حاول مرة أخرى.',
                    'bg-gray-800 p-3 rounded-2xl max-w-[85%] text-red-300'
                );
            } finally {
                sending = false;
                scrollToEnd();
            }
        }
    };

    // Count this page view toward the returning-visitor signal, once per tab session.
    if (!sessionStorage.getItem('aidenCounted')) {
        try {
            sessionStorage.setItem('aidenCounted', '1');
            var n = parseInt(localStorage.getItem('aidenVisitCount') || '0', 10);
            localStorage.setItem('aidenVisitCount', String(n + 1));
        } catch (e) { /* best-effort */ }
    }

    // Self-start on pages that just include this script. Pages that lazy-load it
    // and call init() themselves are unaffected — init() is guarded.
    // Held until after load so the widget never competes with page rendering.
    function boot() {
        window.aidenChat.init();
    }

    if (document.readyState === 'complete') {
        setTimeout(boot, 0);
    } else {
        window.addEventListener('load', function () { setTimeout(boot, 1200); });
    }
})();
