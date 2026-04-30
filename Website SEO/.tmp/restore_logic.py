import os
import re

PUBLIC_HTML = "public_html"
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), PUBLIC_HTML))

# Pages that have the multi-step form
FORM_PAGES = ["services.html", "services-en.html"]
# All pages needing chatbot fix
ALL_PAGES = ["index.html", "services.html", "services-en.html", "contact.html", "contact-en.html"]

def restore_logic(file_path, has_form):
    print(f"Restoring logic: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    is_arabic = 'lang="ar"' in content or 'dir="rtl"' in content
    lang_label = 'ar' if is_arabic else 'en'
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
                    language: '{lang_label}', 
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

    # Final combined JS
    final_js = f"""
    <script>
        {form_js}
        
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

    # Cleanup broken script blocks at the end
    content = re.sub(r'<script>\s*// Chatbot & Menu Logic.*?</script>', '', content, flags=re.DOTALL)
    # Remove the broken tail
    content = re.sub(r'\);\s*\}\s*// ==================== INIT ====================.*?<\/script>', '</script>', content, flags=re.DOTALL)
    content = re.sub(r'<\/script>\s*<\/body>', '</body>', content) # Ensure clean end
    
    # Inject final script
    if "</body>" in content:
        content = content.replace("</body>", final_js + "\n</body>")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

for page in ALL_PAGES:
    restore_logic(os.path.join(BASE_DIR, page), page in FORM_PAGES)

print("Restoration complete.")
