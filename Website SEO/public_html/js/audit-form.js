// ==================== MULTI-STEP AUDIT FORM LOGIC ====================

window.auditForm = {
    init: function() {
        const modal = document.getElementById('auditModal');
        const form = document.getElementById('auditForm');
        if (!form) return;
        
        const steps = Array.from(form.querySelectorAll('.form-step'));
        const progressSteps = Array.from(document.querySelectorAll('.progress-step'));
        let currentStep = 0;
        
        // Bind the actual actions
        window.auditForm.open = function() {
            currentStep = 0;
            showStep(currentStep);
            modal.classList.add('active');
        };
        
        window.auditForm.close = function() {
            modal.classList.remove('active');
        };
        
        function showStep(stepIndex) {
            steps.forEach((step, index) => {
                step.classList.toggle('active', index === stepIndex);
            });
            progressSteps.forEach((pStep, index) => {
                pStep.classList.toggle('active', index <= stepIndex);
            });
        }
        
        function validateStep(stepIndex) {
            const inputs = steps[stepIndex].querySelectorAll('input[required], textarea[required], select[required]');
            let valid = true;
            inputs.forEach(i => {
                if (!i.value.trim()) {
                    i.style.borderColor = '#ef4444';
                    valid = false;
                } else {
                    i.style.borderColor = 'rgba(255,255,255,0.1)';
                }
            });
            return valid;
        }
        
        // Wire up next/prev click listeners
        form.addEventListener('click', (e) => {
            if (e.target.matches('.next')) {
                if (validateStep(currentStep) && currentStep < steps.length - 1) {
                    currentStep++;
                    showStep(currentStep);
                }
            } else if (e.target.matches('.prev') && currentStep > 0) {
                currentStep--;
                showStep(currentStep);
            }
        });
        
        // Slider output updates
        const comfortSlider = document.getElementById('aiComfort');
        const comfortOutput = document.getElementById('aiComfortOutput');
        if (comfortSlider && comfortOutput) {
            comfortOutput.innerText = comfortSlider.value;
            comfortSlider.addEventListener('input', () => {
                comfortOutput.innerText = comfortSlider.value;
            });
        }
        
        // Overlay dismiss listener
        modal.addEventListener('click', (e) => {
            if (e.target === modal) window.auditForm.close();
        });
        
        // Submissions handler
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (!validateStep(currentStep)) return;
            
            const btn = form.querySelector('.nav-btn.submit') || form.querySelector('button[type="submit"]');
            if (!btn) return;
            const originalText = btn.textContent;
            
            const isEn = document.documentElement.lang === 'en';
            btn.textContent = isEn ? 'Sending...' : 'جاري الإرسال...';
            btn.disabled = true;
            
            const formData = {
                fullName: document.getElementById('fullName')?.value || '',
                email: document.getElementById('email')?.value || '',
                phone: document.getElementById('phone')?.value || '',
                company: document.getElementById('company')?.value || '',
                role: document.getElementById('role')?.value || '',
                website: document.getElementById('website')?.value || '',
                industry: document.getElementById('industry')?.value || '',
                employees: document.getElementById('employees')?.value || '',
                revenue: document.getElementById('revenue')?.value || '',
                revenueStreams: document.getElementById('revenueStreams')?.value || '',
                challenges: document.getElementById('challenges')?.value || '',
                goals: document.getElementById('goals')?.value || '',
                pastExperience: document.getElementById('pastExperience')?.value || '',
                aiComfort: document.getElementById('aiComfort')?.value || '',
                processes: Array.from(form.querySelectorAll('input[name="process"]:checked')).map(cb => cb.value).join(', '),
                budget: document.getElementById('budget')?.value || '',
                timeline: document.getElementById('timeline')?.value || '',
                keyQuestion: document.getElementById('keyQuestion')?.value || '',
                submittedAt: new Date().toISOString(),
                language: isEn ? 'en' : 'ar',
                page: window.location.pathname
            };
            
            try {
                let response = await fetch("https://aiden-backend-aiden.up.railway.app/audit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formData)
                });
                let result = await response.json();
                
                if (result.success) {
                    alert(isEn ? 'Form submitted! Redirecting to booking page.' : 'تم إرسال النموذج! جاري تحويلك إلى صفحة الحجز.');
                    window.location.href = "https://calendly.com/ai-profit-lab2026";
                } else {
                    // Fallback try
                    let altResponse = await fetch("https://aiden-backend-aiden.up.railway.app/api/audit", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(formData)
                    });
                    let altResult = await altResponse.json();
                    if (altResult.success) {
                        alert(isEn ? 'Submitted! Redirecting to booking page.' : 'تم الإرسال! تحويلك إلى الحجز.');
                        window.location.href = "https://calendly.com/ai-profit-lab2026";
                    } else {
                        alert(isEn ? 'An error occurred. Please try again.' : 'حدث خطأ. حاول مرة أخرى.');
                    }
                }
            } catch (e) {
                console.error(e);
                alert(isEn ? 'Connection error.' : 'خطأ في الاتصال.');
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
    }
};
