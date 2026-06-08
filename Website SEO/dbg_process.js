
        

                // Close menu when clicking a link
                mobileMenu.querySelectorAll('a').forEach(link => {
                    link.addEventListener('click', function() {
                        mobileMenu.classList.remove('active');
                    });
                });

                // Close when clicking outside
                document.addEventListener('click', function(event) {
                    if (!mobileMenu.contains(event.target) && !toggleBtn.contains(event.target)) {
                        mobileMenu.classList.remove('active');
                    }
                });

                // Optional: close on escape key
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
                        mobileMenu.classList.remove('active');
                    }
                });

        });

        // ==================== MULTI-STEP FORM LOGIC ====================
        const modal = document.getElementById('auditModal');
        const form = document.getElementById('auditForm');
        const steps = Array.from(form.querySelectorAll('.form-step'));
        const progressSteps = Array.from(document.querySelectorAll('.progress-step'));
        let currentStep = 0;

        function openAuditForm() {
            currentStep = 0;
            showStep(currentStep);
            modal.classList.add('active');
        }

        function closeAuditForm() {
            modal.classList.remove('active');
        }

        function showStep(stepIndex) {
            steps.forEach((step, index) => {
                step.classList.toggle('active', index === stepIndex);
            });
            progressSteps.forEach((pStep, index) => {
                pStep.classList.toggle('active', index <= stepIndex);
            });
        }

        function validateStep(stepIndex) {
            const currentStepElement = steps[stepIndex];
            const inputs = currentStepElement.querySelectorAll('input[required], textarea[required]');
            let isValid = true;
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.style.borderColor = '#ef4444';
                    isValid = false;
                } else {
                    input.style.borderColor = 'rgba(255,255,255,0.1)';
                }
            });
            return isValid;
        }
        form.addEventListener('click', (e) => {
            if (e.target.matches('.next')) {
                if (validateStep(currentStep)) {
                    if (currentStep < steps.length - 1) {
                        currentStep++;
                        showStep(currentStep);
                    }
                }
            } else if (e.target.matches('.prev')) {
                if (currentStep > 0) {
                    currentStep--;
                    showStep(currentStep);
                }
            }
        });

        // Slider
        const comfortSlider = document.getElementById('aiComfort');
        const comfortOutput = document.getElementById('aiComfortOutput');
        if (comfortSlider && comfortOutput) {
            comfortOutput.innerText = comfortSlider.value;
            comfortSlider.addEventListener('input', function() {
                comfortOutput.innerText = this.value;
            });
        }

        // Form Submit
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            if (!validateStep(currentStep)) return;

            const submitBtn = document.querySelector('.nav-btn.submit');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'جاري الإرسال...';
            submitBtn.disabled = true;

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
                processes: Array.from(document.querySelectorAll('input[name="process"]:checked')).map(cb => cb.value).join(', '),
                source: Array.from(document.querySelectorAll('input[name="source"]:checked')).map(cb => cb.value).join(', '),
                otherSource: document.getElementById('otherSource')?.value || '',
                budget: document.getElementById('budget')?.value || '',
                timeline: document.getElementById('timeline')?.value || '',
                keyQuestion: document.getElementById('keyQuestion')?.value || '',
                language: 'ar',
                page: window.location.pathname,
                submittedAt: new Date().toISOString()
            };

            try {
                const response = await fetch("https://aiden-backend-aiden.up.railway.app/audit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formData)
                });
                const result = await response.json();
                if (result.success) {
                    alert('تم إرسال النموذج! جاري تحويلك إلى صفحة الحجز.');
                    window.location.href = "https://calendly.com/ai-profit-lab2026";
                } else {
                    alert("حدث خطأ. الرجاء المحاولة مرة أخرى.");
                }
            } catch (error) {
                alert("خطأ في الاتصال. تحقق من اتصالك بالإنترنت.");
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });

        modal.addEventListener('click', (event) => {
            if (event.target === modal) closeAuditForm();
        });

        // ==================== COUNTRY DETECTION ====================
        async function detectCountry() {
            try {
                const response = await fetch('https://ipapi.co/json/');
                const data = await response.json();
                const country = data.country_name || 'عمان';
                const countryCode = data.country_code || 'OM';
                localStorage.setItem('visitorCountry', country);
                localStorage.setItem('visitorCountryCode', countryCode);
                document.getElementById('visitor-country').textContent = countryCode;
                document.getElementById('welcome-message').textContent = `مرحباً بك من ${country}!`;
            } catch (error) {
                console.log('Country detection failed');
            }
        }

        // ==================== CHAT FUNCTIONS ====================
        async function handleSend() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;
            
            const box = document.getElementById('chat-messages');
            
            let visitorId = localStorage.getItem('aidenVisitorId');
            if (!visitorId) {
                visitorId = 'visitor_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('aidenVisitorId', visitorId);
            }

            box.innerHTML += `<div class="bg-blue-900/50 mr-auto p-3 rounded-2xl rounded-bl-none max-w-[85%] text-white">${message}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;
            
            box.innerHTML += `<div id="typing-indicator" class="bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-[85%] text-gray-300">...</div>`;
            
            try {
                const response = await fetch('https://aiden-backend-aiden.up.railway.app/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, sessionId: visitorId, language: 'ar' })
                });
                const result = await response.json();
                document.getElementById('typing-indicator')?.remove();
                const reply = result.reply || result.response || 'شكراً لرسالتك!';
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-[85%] text-gray-300">${reply}</div>`;
            } catch (error) {
                document.getElementById('typing-indicator')?.remove();
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-[85%] text-red-300">عذراً، حدث خطأ</div>`;
            }
            box.scrollTop = box.scrollHeight;
        }

        function toggleChat() {
            const chat = document.getElementById('aiden-ui');
            if (chat) chat.classList.toggle('active');
        }

        // ==================== INIT ====================
        window.addEventListener('load', async function() {
            await detectCountry();
            if (!sessionStorage.getItem('aidenPopped')) {
                setTimeout(() => {
                    const chat = document.getElementById('aiden-ui');
                    if (chat && !chat.classList.contains('active')) {
                        toggleChat();
                        sessionStorage.setItem('aidenPopped', 'true');
                    }
                }, 10000);
            }
        });
