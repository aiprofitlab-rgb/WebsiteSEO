// ==================== AIDEN CHATBOT WIDGET CONTROLLER ====================

window.aidenChat = {
    init: function() {
        detectCountry();
    },
    toggle: function() {
        const chat = document.getElementById('aiden-ui');
        if (!chat) return;
        chat.classList.toggle('active');
        if (chat.classList.contains('active')) {
            const msgs = document.getElementById('chat-messages');
            const greeting = getPageSpecificGreeting();
            const welcomeMsg = document.getElementById('welcome-message')?.textContent || '';
            if (msgs && msgs.children.length <= 1) {
                msgs.innerHTML = `<div class="bg-gray-800 p-4 rounded-2xl rounded-tr-none max-w-[85%]">${greeting} <span class="block text-xs text-gray-500 mt-1">${welcomeMsg}</span></div>`;
            }
        }
    },
    send: async function() {
        const input = document.getElementById('user-input');
        if (!input) return;
        const msg = input.value.trim();
        if (!msg) return;
        const box = document.getElementById('chat-messages');
        if (!box) return;
        
        let vid = localStorage.getItem('aidenVisitorId') || ('visitor_'+Date.now()+'_'+Math.random().toString(36).substr(2,9));
        if (!localStorage.getItem('aidenVisitorId')) {
            localStorage.setItem('aidenVisitorId', vid);
            localStorage.setItem('aidenVisitCount', '1');
            localStorage.setItem('aidenFirstVisit', new Date().toISOString());
        }
        let vc = parseInt(localStorage.getItem('aidenVisitCount') || '1');
        localStorage.setItem('aidenVisitCount', vc + 1);
        let country = localStorage.getItem('visitorCountry') || (document.documentElement.lang === 'en' ? 'Oman' : 'عمان');
        let code = localStorage.getItem('visitorCountryCode') || 'OM';
        let chatEmail = localStorage.getItem('aidenVisitorEmail') || (`visitor_${vid}@aiprofitlab.local`);
        if (!localStorage.getItem('aidenVisitorEmail')) {
            localStorage.setItem('aidenVisitorEmail', chatEmail);
        }
        
        const isEn = document.documentElement.lang === 'en';
        
        // Add user bubble
        box.innerHTML += `<div class="bg-blue-900/50 mr-auto p-3 rounded-2xl rounded-bl-none max-w-[85%] text-white">${msg}</div>`;
        input.value = '';
        requestAnimationFrame(() => { box.scrollTop = box.scrollHeight; });
        
        // Add typing indicator
        box.innerHTML += `<div id="typing-indicator" class="bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-[85%] text-gray-300">...</div>`;
        requestAnimationFrame(() => { box.scrollTop = box.scrollHeight; });
        
        try {
            const response = await fetch('https://aiden-backend-aiden.up.railway.app/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: msg,
                    sessionId: vid,
                    email: chatEmail,
                    language: isEn ? 'en' : 'ar',
                    country: country,
                    countryCode: code,
                    page: window.location.pathname,
                    visitCount: vc,
                    isReturning: vc > 1,
                    previousVisits: vc - 1,
                    firstVisit: localStorage.getItem('aidenFirstVisit')
                })
            });
            const result = await response.json();
            document.getElementById('typing-indicator')?.remove();
            const reply = result.reply || result.response || (isEn ? 'Thank you for your message!' : 'شكراً لرسالتك! دعنا نكمل.');
            box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-[85%] text-gray-300">${reply}</div>`;
        } catch(e) {
            document.getElementById('typing-indicator')?.remove();
            box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-[85%] text-red-300">${isEn ? 'Connection error. Try again.' : 'عذراً، حدث خطأ. حاول مرة أخرى.'}</div>`;
        }
        requestAnimationFrame(() => { box.scrollTop = box.scrollHeight; });
    }
};

async function detectCountry() {
    try {
        const response = await fetch('https://ipapi.co/json/');
        const data = await response.json();
        const country = data.country_name || (document.documentElement.lang === 'en' ? 'Oman' : 'عمان');
        const code = data.country_code || 'OM';
        localStorage.setItem('visitorCountry', country);
        localStorage.setItem('visitorCountryCode', code);
        const span = document.getElementById('visitor-country');
        if (span) span.textContent = code;
        const welcome = document.getElementById('welcome-message');
        if (welcome) {
            welcome.textContent = document.documentElement.lang === 'en' ? `Welcome from ${country}!` : `مرحباً بك من ${country}!`;
        }
    } catch(e) {
        console.log('Country detection failed');
    }
}

function getPageSpecificGreeting() {
    const path = window.location.pathname;
    const isEn = document.documentElement.lang === 'en';
    if (path.includes('services')) {
        return isEn ? 'Which package seems right for your business? I can explain the details.' : 'أي باقة تبدو مناسبة لعملك؟ يمكنني شرح التفاصيل.';
    }
    if (path.includes('process')) {
        return isEn ? 'Our process is simple: Discover, Build, Support. Which step would you like to understand better?' : 'طريقتنا بسيطة: نكتشف، نبني، ندعم. أي خطوة تود فهمها أكثر؟';
    }
    if (path.includes('contact')) {
        return isEn ? 'You can contact us directly, or write your question now.' : 'يمكنك التواصل معنا مباشرة، أو اكتب سؤالك الآن.';
    }
    if (path.includes('about')) {
        return isEn ? 'We build smart systems for GCC businesses. What would you like to know about us?' : 'نبني أنظمة ذكية للشركات العمانية. ماذا تريد أن تعرف عنا؟';
    }
    return isEn ? 'Hello! How can I help you today?' : 'مرحباً! كيف يمكنني مساعدتك اليوم؟';
}
