
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

        // Main Audit Form Submit
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            if (!validateStep(currentStep)) return;

            const submitBtn = document.querySelector('.nav-btn.submit');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Sending...';
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
                language: 'en',
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
                    alert('Form submitted! Redirecting to Calendly...');
                    window.location.href = "https://calendly.com/ai-profit-lab2026";
                } else {
                    alert("An error occurred. Please try again.");
                }
            } catch (error) {
                alert("Connection error. Please check your internet.");
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });

        // Quick Contact Form
        const quickForm = document.getElementById('quickContactForm');
        if (quickForm) {
            quickForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const submitBtn = this.querySelector('button');
                const originalText = submitBtn.textContent;
                
                submitBtn.textContent = 'Sending...';
                submitBtn.disabled = true;
                
                const quickData = {
                    fullName: document.getElementById('quickName').value,
                    email: document.getElementById('quickEmail').value,
                    message: document.getElementById('quickMessage').value,
                    source: 'quick_contact',
                    language: 'en',
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
                        alert('Message sent! We\'ll get back to you within 24 hours.');
                        quickForm.reset();
                    } else {
                        alert('Something went wrong. Please try again or use the call booking form.');
                    }
                } catch (error) {
                    alert('Connection error. Please try again.');
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
                const country = data.country_name || 'Unknown';
                const countryCode = data.country_code || 'XX';
                localStorage.setItem('visitorCountry', country);
                localStorage.setItem('visitorCountryCode', countryCode);
                document.getElementById('visitor-country').textContent = countryCode;
                document.getElementById('welcome-message').textContent = `Welcome from ${country}!`;
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

            box.innerHTML += `<div class="bg-blue-900/50 ml-auto p-3 rounded-2xl rounded-br-none max-w-[85%] text-white">${message}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;
            
            box.innerHTML += `<div id="typing-indicator" class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-gray-300">...</div>`;
            
            try {
                const response = await fetch('https://aiden-backend-aiden.up.railway.app/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message, 
                        sessionId: visitorId, 
                        language: 'en',
                        page: window.location.pathname 
                    })
                });
                const result = await response.json();
                document.getElementById('typing-indicator')?.remove();
                const reply = result.reply || result.response || 'Thanks for your message!';
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-gray-300">${reply}</div>`;
            } catch (error) {
                document.getElementById('typing-indicator')?.remove();
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-red-300">Sorry, please try again</div>`;
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
