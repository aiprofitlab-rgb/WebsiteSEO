
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
            const inputs = currentStepElement.querySelectorAll('input[required], textarea[required], select[required]');
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

        // Slider for AI Comfort
        const comfortSlider = document.getElementById('aiComfort');
        const comfortOutput = document.getElementById('aiComfortOutput');
        if (comfortSlider && comfortOutput) {
            comfortOutput.innerText = comfortSlider.value;
            comfortSlider.addEventListener('input', function() {
                comfortOutput.innerText = this.value;
            });
        }

        // FORM SUBMIT
        form.addEventListener('submit', async function(event) {
            event.preventDefault();

            if (!validateStep(currentStep)) return;

            const submitBtn = document.querySelector('.nav-btn.submit');
            const originalText = submitBtn.textContent;
            const lang = document.documentElement.lang || 'en';
            
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
                submittedAt: new Date().toISOString(),
                language: lang,
                page: window.location.pathname,
                userAgent: navigator.userAgent
            };

            try {
                const response = await fetch("https://aiden-backend-aiden.up.railway.app/audit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formData)
                });
                const result = await response.json();
                if (result.success) {
                    alert('Form submitted successfully! Redirecting to Calendly...');
                    window.location.href = "https://calendly.com/ai-profit-lab2026";
                } else {
                    const altResponse = await fetch("https://aiden-backend-aiden.up.railway.app/api/audit", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(formData)
                    });
                    const altResult = await altResponse.json();
                    if (altResult.success) {
                        alert('Form submitted successfully! Redirecting to Calendly...');
                        window.location.href = "https://calendly.com/ai-profit-lab2026";
                    } else {
                        alert("An error occurred. Please try again.");
                    }
                }
            } catch (error) {
                console.error('Submission error:', error);
                alert("Connection error. Please check your internet.");
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
                const country = data.country_name || 'Oman';
                const countryCode = data.country_code || 'OM';
                localStorage.setItem('visitorCountry', country);
                localStorage.setItem('visitorCountryCode', countryCode);
                const countrySpan = document.getElementById('visitor-country');
                if (countrySpan) countrySpan.textContent = countryCode;
                const welcomeMsg = document.getElementById('welcome-message');
                if (welcomeMsg) {
                    if (countryCode === 'OM') {
                        welcomeMsg.textContent = 'Welcome from Oman!';
                    } else if (countryCode === 'SA') {
                        welcomeMsg.textContent = 'Welcome from Saudi Arabia!';
                    } else if (countryCode === 'AE') {
                        welcomeMsg.textContent = 'Welcome from UAE!';
                    } else if (countryCode === 'QA') {
                        welcomeMsg.textContent = 'Welcome from Qatar!';
                    } else if (countryCode === 'KW') {
                        welcomeMsg.textContent = 'Welcome from Kuwait!';
                    } else {
                        welcomeMsg.textContent = `Welcome from ${country}!`;
                    }
                }
                return { country, countryCode };
            } catch (error) {
                console.log('Country detection failed, defaulting to Oman');
                return { country: 'Oman', countryCode: 'OM' };
            }
        }

        // ==================== PAGE-SPECIFIC CHAT GREETINGS ====================
        function getPageSpecificGreeting() {
            const path = window.location.pathname;
            if (path.includes('services')) {
                return 'Which package looks right for your business? I can explain the details.';
            } else if (path.includes('process')) {
                return 'Our process is simple: Discover, Build, Launch. Which step would you like to understand better?';
            } else if (path.includes('contact')) {
                return 'You can contact us directly, or ask me your question now.';
            } else if (path.includes('about')) {
                return 'We build smart systems for Omani businesses. What would you like to know about us?';
            } else {
                return 'Hello! How can I help you today?';
            }
        }

        // ==================== CHAT FUNCTIONS ====================
        async function handleSend() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;
            const box = document.getElementById('chat-messages');
            let visitorId = localStorage.getItem('aidenVisitorId');
            let visitCount = localStorage.getItem('aidenVisitCount');
            let firstVisit = localStorage.getItem('aidenFirstVisit');
            if (!visitorId) {
                visitorId = 'visitor_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                visitCount = '1';
                firstVisit = new Date().toISOString();
                localStorage.setItem('aidenVisitorId', visitorId);
                localStorage.setItem('aidenVisitCount', visitCount);
                localStorage.setItem('aidenFirstVisit', firstVisit);
            } else {
                visitCount = (parseInt(visitCount) + 1).toString();
                localStorage.setItem('aidenVisitCount', visitCount);
            }
            const country = localStorage.getItem('visitorCountry') || 'Oman';
            const countryCode = localStorage.getItem('visitorCountryCode') || 'OM';
            let chatEmail = localStorage.getItem('aidenVisitorEmail');
            if (!chatEmail) {
                chatEmail = `visitor_${visitorId}@aiprofitlab.local`;
                localStorage.setItem('aidenVisitorEmail', chatEmail);
            }
            box.innerHTML += `<div class="bg-blue-900/50 ml-auto p-3 rounded-2xl rounded-br-none max-w-[85%] text-white">${message}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;
            box.innerHTML += `<div id="typing-indicator" class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-gray-300">...</div>`;
            try {
                const requestBody = {
                    message: message,
                    sessionId: visitorId,
                    email: chatEmail,
                    language: 'en',
                    country: country,
                    countryCode: countryCode,
                    page: window.location.pathname,
                    visitCount: visitCount,
                    isReturning: parseInt(visitCount) > 1,
                    previousVisits: parseInt(visitCount) - 1,
                    firstVisit: firstVisit
                };
                const response = await fetch('https://aiden-backend-aiden.up.railway.app/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });
                const result = await response.json();
                document.getElementById('typing-indicator')?.remove();
                const reply = result.reply || result.response || 'Thanks for your message! Let\'s continue.';
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-gray-300">${reply}</div>`;
            } catch (error) {
                console.error('Chat error:', error);
                document.getElementById('typing-indicator')?.remove();
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-red-300">Sorry, please try again</div>`;
            }
            box.scrollTop = box.scrollHeight;
        }

        function toggleChat() {
            const chat = document.getElementById('aiden-ui');
            chat.classList.toggle('active');
            if (chat.classList.contains('active')) {
                const chatMessages = document.getElementById('chat-messages');
                const greeting = getPageSpecificGreeting();
                const welcomeMsg = document.getElementById('welcome-message')?.textContent || '';
                if (chatMessages.children.length === 1) {
                    chatMessages.innerHTML = `<div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none max-w-[85%]">${greeting} <span class="block text-xs text-gray-500 mt-1">${welcomeMsg}</span></div>`;
                }
            }
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
    