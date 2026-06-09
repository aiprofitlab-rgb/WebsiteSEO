// ==================== MAIN INTERACTIVE LAYOUT & NAV JS ====================

// Schedule non-critical DOM initialization to yield main thread for FCP
const scheduleTask = (task) => {
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => task(), { timeout: 2000 });
    } else {
        setTimeout(task, 0);
    }
};

const initMain = () => {
    // YouTube Facade Play logic
    const facade = document.querySelector('.youtube-facade');
    if (facade) {
        facade.addEventListener('click', function() {
            const videoId = this.getAttribute('data-videoid');
            const iframe = document.createElement('iframe');
            iframe.setAttribute('src', `https://www.youtube-nocookie.com/embed/${videoId}?rel=0&modestbranding=1&autoplay=1`);
            iframe.setAttribute('frameborder', '0');
            iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
            iframe.setAttribute('allowfullscreen', 'true');
            iframe.className = 'w-full h-full absolute inset-0';
            this.innerHTML = '';
            this.appendChild(iframe);
        });
    }

    // FIXED: MOBILE MENU TOGGLE (Unified System)
    const mobileToggleBtn = document.getElementById('mobileMenuToggle');
    const mobileMenuDropdown = document.getElementById('mobileDropdownMenu');
    
    if (mobileToggleBtn && mobileMenuDropdown) {
        mobileToggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            mobileMenuDropdown.classList.toggle('open');
        });
        
        // Close menu when clicking any link inside
        mobileMenuDropdown.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileMenuDropdown.classList.remove('open');
            });
        });
        
        // Close if user clicks outside
        document.addEventListener('click', function(event) {
            if (!mobileToggleBtn.contains(event.target) && !mobileMenuDropdown.contains(event.target)) {
                mobileMenuDropdown.classList.remove('open');
            }
        });
    }

    // STANDARD NAV JS
    const btn = document.getElementById('mobileToggle');
    const m = document.getElementById('mobileMenu');
    if (btn && m) {
        const toggleAction = (e) => {
            e.preventDefault();
            e.stopPropagation();
            m.classList.toggle('open');
        };
        
        btn.onclick = toggleAction;
        btn.ontouchstart = toggleAction;
        
        document.addEventListener('click', (e) => {
            if (m.classList.contains('open') && !btn.contains(e.target) && !m.contains(e.target)) {
                m.classList.remove('open');
            }
        });
    }

    // Quick Contact Form Submission Handler
    const quickForm = document.getElementById('quickContactForm');
    if (quickForm) {
        quickForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button');
            const originalText = submitBtn.textContent;
            
            submitBtn.textContent = document.documentElement.lang === 'en' ? 'Sending...' : 'جاري الإرسال...';
            submitBtn.disabled = true;
            
            const quickData = {
                fullName: document.getElementById('quickName')?.value || '',
                email: document.getElementById('quickEmail')?.value || '',
                message: document.getElementById('quickMessage')?.value || '',
                source: 'quick_contact',
                language: document.documentElement.lang || 'ar',
                page: window.location.pathname,
                submittedAt: new Date().toISOString()
            };
            
            try {
                const response = await fetch("https://aiden-backend-aiden.up.railway.app/contact", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(quickData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(document.documentElement.lang === 'en' ? 'Message sent! We will reply within 24 hours.' : 'تم إرسال الرسالة! سنرد عليك خلال ٢٤ ساعة.');
                    quickForm.reset();
                } else {
                    alert(document.documentElement.lang === 'en' ? 'An error occurred. Please try again.' : 'حدث خطأ. الرجاء المحاولة مرة أخرى.');
                }
            } catch (error) {
                alert(document.documentElement.lang === 'en' ? 'Connection error. Try again.' : 'خطأ في الاتصال. حاول مرة أخرى.');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // Lazy-load Google Tag Manager (GTM)
    lazyLoadGTM();
};

// Global GTM lazy loader
const lazyLoadGTM = () => {
    if (window.gtag_initialized) return;
    window.gtag_initialized = true;

    // Define GTM placeholder queue
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function() { dataLayer.push(arguments); };

    setTimeout(() => {
        const s = document.createElement('script');
        s.src = "https://www.googletagmanager.com/gtag/js?id=G-2GPVY4Z5KR";
        s.async = true;
        s.onload = () => {
            gtag('js', new Date());
            gtag('config', 'G-2GPVY4Z5KR');
        };
        document.body.appendChild(s);
    }, 3000);
};

// Listen with requestIdleCallback schedule
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => scheduleTask(initMain));
} else {
    scheduleTask(initMain);
}
