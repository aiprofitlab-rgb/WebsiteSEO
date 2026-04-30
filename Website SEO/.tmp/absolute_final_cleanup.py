import os
import re

PUBLIC_HTML = "public_html"
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), PUBLIC_HTML))

PAGES = [
    "index.html", "services.html", "services-en.html", "process.html", "process-en.html", 
    "contact.html", "contact-en.html", "about.html", "about-en.html",
    "blog_ar.html", "academy_ar.html", "blog.html", "academy.html"
]

def final_cleanup(file_path):
    print(f"Final cleanup: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    is_arabic = 'lang="ar"' in content or 'dir="rtl"' in content
    has_form = "auditForm" in content
    has_youtube = "youtube-facade" in content
    
    # --- 1. Clean up CSS (Fix visible text issue and redundancy) ---
    # Wrap any stray UNIFIED NAVIGATION STYLES in <style> if needed, or just clean them
    # First, let's remove ALL style blocks and re-inject a clean one to be safe
    # Actually, let's just target the problematic stray text in index.html
    if "index.html" in file_path:
        content = content.replace("/* ========== UNIFIED NAVIGATION STYLES ========== */", "<style>\n/* ========== UNIFIED NAVIGATION STYLES ========== */")
        # Fix the possible duplicate style tag that might have been created
        content = content.replace("<style>\n<style>", "<style>")

    # --- 2. Clean up Scripts (The main mess) ---
    # Find everything between the last significant HTML element and </body>
    # We want to remove all script blocks there.
    
    # More robust: remove all <script> blocks that contain "toggleChat" or "mobileMenuToggle"
    script_pattern = re.compile(r'<script>.*?(toggleChat|mobileMenuToggle|detectCountry).*?</script>', re.DOTALL)
    content = script_pattern.sub('', content)
    
    # Also remove any YouTube facade scripts if we're re-injecting them
    if has_youtube:
        yt_pattern = re.compile(r'<script>.*?youtube-facade.*?</script>', re.DOTALL)
        content = yt_pattern.sub('', content)

    # Now define the CLEAN Logic
    lang_code = 'ar' if is_arabic else 'en'
    submit_text = 'جاري الإرسال...' if is_arabic else 'Sending...'
    success_msg = 'تم إرسال النموذج! جاري تحويلك إلى صفحة الحجز.' if is_arabic else 'Form submitted! Redirecting to booking page.'
    
    # Form Logic
    form_js = ""
    if has_form:
        form_js = f"""
    // Multi-step Form Logic
    const modal = document.getElementById('auditModal');
    const form = document.getElementById('auditForm');
    if (modal && form) {{
        const steps = Array.from(form.querySelectorAll('.form-step'));
        const progressSteps = Array.from(document.querySelectorAll('.progress-step'));
        let currentStep = 0;
        
        window.openAuditForm = function() {{ currentStep = 0; showStep(currentStep); modal.classList.add('active'); }};
        window.closeAuditForm = function() {{ modal.classList.remove('active'); }};
        
        function showStep(stepIndex) {{ 
            steps.forEach((step, index) => {{ step.classList.toggle('active', index === stepIndex); }}); 
            progressSteps.forEach((pStep, index) => {{ pStep.classList.toggle('active', index <= stepIndex); }}); 
        }}
        
        function validateStep(stepIndex) {{ 
            const inputs = steps[stepIndex].querySelectorAll('input[required], textarea[required], select[required]'); 
            let valid = true; 
            inputs.forEach(i => {{ 
                if (!i.value.trim()) {{ i.style.borderColor = '#ef4444'; valid = false; }} 
                else i.style.borderColor = 'rgba(255,255,255,0.1)'; 
            }}); 
            return valid; 
        }}
        
        form.addEventListener('click', (e) => {{ 
            if (e.target.matches('.next')) {{ 
                if (validateStep(currentStep) && currentStep < steps.length-1) {{ currentStep++; showStep(currentStep); }} 
            }} else if (e.target.matches('.prev') && currentStep > 0) {{ 
                currentStep--; showStep(currentStep); 
            }} 
        }});
        
        form.addEventListener('submit', async (event) => {{ 
            event.preventDefault(); 
            if(!validateStep(currentStep)) return; 
            const btn = document.querySelector('.nav-btn.submit'); 
            const original = btn.textContent; 
            btn.textContent = '{submit_text}'; 
            btn.disabled = true; 
            
            const formData = {{ 
                fullName: document.getElementById('fullName')?.value||'', 
                email: document.getElementById('email')?.value||'', 
                phone: document.getElementById('phone')?.value||'', 
                submittedAt: new Date().toISOString(), 
                language: '{lang_code}', 
                page: window.location.pathname 
            }}; 
            
            try {{ 
                let res = await fetch("https://aiden-backend-aiden.up.railway.app/audit", {{ 
                    method: "POST", 
                    headers: {{ "Content-Type": "application/json" }}, 
                    body: JSON.stringify(formData) 
                }}); 
                alert('{success_msg}'); 
                window.location.href = "https://calendly.com/ai-profit-lab2026";
            }} catch(e) {{ 
                console.error(e); 
                alert("Connection error."); 
            }} finally {{ 
                btn.textContent = original; 
                btn.disabled = false; 
            }} 
        }});
        
        modal.addEventListener('click', (e) => {{ if(e.target === modal) closeAuditForm(); }});
    }}
"""

    youtube_js = ""
    if has_youtube:
        youtube_js = """
    // YouTube Facade Logic
    document.addEventListener('DOMContentLoaded', () => {
        const facades = document.querySelectorAll('.youtube-facade');
        facades.forEach(facade => {
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
        });
    });
"""

    # Final Combined Script Block
    final_script = f"""
<script>
    {form_js}
    {youtube_js}

    // Chatbot Logic
    function toggleChat() {{ 
        const chat = document.getElementById('aiden-ui'); 
        if (!chat) return;
        chat.classList.toggle('active'); 
        if(chat.classList.contains('active')) {{ 
            const msgs = document.getElementById('chat-messages'); 
            const greeting = (typeof getPageSpecificGreeting === 'function') ? getPageSpecificGreeting() : 'Hello!'; 
            const welcomeMsg = document.getElementById('welcome-message')?.textContent || ''; 
            if(msgs && msgs.children.length === 1) {{
                msgs.innerHTML = `<div class="bg-gray-800 p-4 rounded-2xl rounded-tr-none max-w-[85%]">${{greeting}} <span class="block text-xs text-gray-500 mt-1">${{welcomeMsg}}</span></div>`; 
            }}
        }} 
    }}

    // Unified Menu Logic
    (function() {{
        const mobileToggleBtn = document.getElementById('mobileMenuToggle');
        const mobileMenuDropdown = document.getElementById('mobileDropdownMenu');
        if (mobileToggleBtn && mobileMenuDropdown) {{
            mobileToggleBtn.addEventListener('click', (e) => {{ e.stopPropagation(); mobileMenuDropdown.classList.toggle('open'); }});
            document.addEventListener('click', (e) => {{ if (!mobileToggleBtn.contains(e.target) && !mobileMenuDropdown.contains(e.target)) mobileMenuDropdown.classList.remove('open'); }});
            mobileMenuDropdown.querySelectorAll('a').forEach(link => {{ link.addEventListener('click', () => mobileMenuDropdown.classList.remove('open')); }});
        }}
    }})();

    window.onload = async () => {{ 
        if (typeof detectCountry === 'function') await detectCountry(); 
        if(!sessionStorage.getItem('aidenPopped')) {{ 
            setTimeout(() => {{ 
                const chat = document.getElementById('aiden-ui'); 
                if(chat && !chat.classList.contains('active')) {{ 
                    toggleChat(); 
                    sessionStorage.setItem('aidenPopped','true'); 
                }} 
            }}, 10000); 
        }} 
    }};
</script>
"""
    
    # Inject before </body>
    if "</body>" in content:
        # Final cleanup of any duplicate </body> tags or weirdness
        content = content.replace("</body>", final_script + "\n</body>")
    
    # Last sanity check: remove any double script tags
    content = content.replace("</script>\n<script>", "")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    for page in PAGES:
        path = os.path.join(BASE_DIR, page)
        if os.path.exists(path):
            final_cleanup(path)
    print("Cleanup complete.")
