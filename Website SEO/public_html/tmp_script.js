
        // STANDARD NAV JS
        (function() {
            function initNav() {
                const btn = document.getElementById('mobileToggle');
                const m = document.getElementById('mobileMenu');
                if (!btn || !m) return;
                
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
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initNav);
            } else {
                initNav();
            }
            window.addEventListener('load', initNav);
        })();
