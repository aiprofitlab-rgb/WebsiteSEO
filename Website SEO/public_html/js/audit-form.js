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
        
        /** Bilingual field label for the hand-off message. */
        function label(en, ar) {
            return (document.documentElement.lang === 'en' ? en : ar) + ': ';
        }

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
            
            // The two POSTs that used to live here went to a Railway host
            // that no longer exists. Every path on it answers with a JSON 404,
            // so response.json() resolved, result.success was undefined, and
            // the handler fell through to alert('An error occurred') - after
            // the visitor had typed out challenges, goals, budget and
            // timeline. Nothing was ever stored. There is no server to store
            // it in, so the lead is handed straight to a channel that works:
            // WhatsApp carries the answers, Calendly takes the booking.
            try {
                const lines = [
                    isEn ? 'Free AI Strategy Audit' : 'التدقيق المجاني لاستراتيجية الذكاء الاصطناعي',
                    '',
                    label('Name', 'الاسم') + formData.fullName,
                    label('Email', 'البريد') + formData.email,
                    label('Phone', 'الهاتف') + formData.phone,
                    label('Company', 'الشركة') + formData.company,
                    label('Role', 'الدور') + formData.role,
                    label('Website', 'الموقع') + formData.website,
                    label('Industry', 'القطاع') + formData.industry,
                    label('Employees', 'عدد الموظفين') + formData.employees,
                    label('Revenue', 'الإيرادات') + formData.revenue,
                    label('Revenue streams', 'مصادر الإيرادات') + formData.revenueStreams,
                    label('Challenges', 'التحديات') + formData.challenges,
                    label('Goals', 'الأهداف') + formData.goals,
                    label('Past experience', 'تجارب سابقة') + formData.pastExperience,
                    label('Comfort with AI (1-10)', 'مستوى الإلمام (1-10)') + formData.aiComfort,
                    label('Processes to automate', 'العمليات المطلوب أتمتتها') + formData.processes,
                    label('Budget', 'الميزانية') + formData.budget,
                    label('Timeline', 'الإطار الزمني') + formData.timeline,
                    label('Key question', 'السؤال الأهم') + formData.keyQuestion,
                    '',
                    label('Page', 'الصفحة') + formData.page
                ].filter(line => !/: $/.test(line));

                const wa = 'https://api.whatsapp.com/send?phone=96899245250&text=' +
                    encodeURIComponent(lines.join('\n'));

                // Opened before the redirect so the answers survive it. If the
                // popup is blocked the Calendly booking still goes ahead.
                window.open(wa, '_blank', 'noopener');
                window.location.href = 'https://calendly.com/ai-profit-lab2026';
            } catch (e) {
                console.error(e);
                window.location.href = 'https://calendly.com/ai-profit-lab2026';
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
    }
};
