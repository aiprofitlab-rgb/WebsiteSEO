import os, re

# The main form script has same broken pattern in about.html, contact.html, process.html and EN variants
# Pattern: many unclosed functions - same as en/index.html was

FORM_SCRIPT_BROKEN_AR = r"/ ==================== MULTI-STEP FORM LOGIC ====================\s*const modal = document\.getElementById\('auditModal'\);\s*const form = document\.getElementById\('auditForm'\);\s*const steps = Array\.from\(form\.querySelectorAll\('\.form-step'\)\);\s*const progressSteps = Array\.from\(document\.querySelectorAll\('\.progress-step'\)\);\s*let currentStep = 0;"

# Check if AR form script is broken (missing function closing braces)
def is_form_broken(script):
    return ("function openAuditForm() {" in script and 
            "function closeAuditForm() {" in script and
            script.count("}") < script.count("{") - 2)  # many unclosed braces

# Fixed versions per language
AR_FORM_SCRIPT_FIXED = """        // ==================== MULTI-STEP FORM LOGIC ====================
        const modal = document.getElementById('auditModal');
        const form = document.getElementById('auditForm');
        const steps = Array.from(form.querySelectorAll('.form-step'));
        const progressSteps = Array.from(document.querySelectorAll('.progress-step'));
        let currentStep = 0;

        function openAuditForm(pkg='') {
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
            const inputs = steps[stepIndex].querySelectorAll('input[required], textarea[required]');
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
        }"""

EN_FORM_SCRIPT_FIXED = """        // ==================== MULTI-STEP FORM LOGIC ====================
        const modal = document.getElementById('auditModal');
        const form = document.getElementById('auditForm');
        const steps = Array.from(form.querySelectorAll('.form-step'));
        const progressSteps = Array.from(document.querySelectorAll('.progress-step'));
        let currentStep = 0;

        function openAuditForm(pkg='') {
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
            const inputs = steps[stepIndex].querySelectorAll('input[required], textarea[required], select[required]');
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
        }"""

# The broken form block pattern for AR pages (just the top broken part up to validateStep)
AR_FORM_BROKEN_TOP = r"/ ==================== MULTI-STEP FORM LOGIC ====================([\s\S]*?)function validateStep\(stepIndex\) \{([\s\S]*?)return isValid;\s*\n"

# Fix the mobile menu script #7 which got partially fixed but has a doubled section
MOBILE_DOUBLED_PATTERN = r"""(// Close menu when clicking any link inside
                mobileMenuDropdown\.querySelectorAll\('a'\)\.forEach\(link => \{
                    link\.addEventListener\('click', \(\) => \{
                        mobileMenuDropdown\.classList\.remove\('open'\);
                    \}
                \}\);
            \}
        \}\);
                
                // Close if user clicks outside
                document\.addEventListener\('click', function\(event\) \{
                    if \(!mobileToggleBtn\.contains\(event\.target\) && !mobileMenuDropdown\.contains\(event\.target\)\) \{
                        mobileMenuDropdown\.classList\.remove\('open'\);
                    \}
                \}\);
            \}
        \}\);)"""

MOBILE_DOUBLED_FIXED = """// Close menu when clicking any link inside
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
        });"""

files = [
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process-en.html',
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    is_en = '-en.html' in filepath
    
    # Fix: broken validateStep (missing } for else and for function)  
    # Pattern: else {\n                    input.style.borderColor = 'rgba...';\n\n            });\n            return isValid;\n\n        form.addEventListener
    if is_en:
        content = re.sub(
            r"(input\.style\.borderColor = 'rgba\(255,255,255,0\.1\)';)\s*\n\s*\}\);\s*\n\s*return isValid;\s*\n",
            r"\1\n                }\n            });\n            return isValid;\n        }\n",
            content
        )
    else:
        content = re.sub(
            r"(input\.style\.borderColor = 'rgba\(255,255,255,0\.1\)';)\s*\n\s*\n\s*\}\);\s*\n\s*return isValid;\s*\n",
            r"\1\n                }\n            });\n            return isValid;\n        }\n",
            content
        )
    
    # Fix: missing } for openAuditForm
    content = re.sub(
        r"(modal\.classList\.add\('active'\);)\s*\n\s*\n\s*function closeAuditForm",
        r"\1\n        }\n\n        function closeAuditForm",
        content
    )
    
    # Fix: missing } for closeAuditForm
    content = re.sub(
        r"(modal\.classList\.remove\('active'\);)\s*\n\s*\n\s*function showStep",
        r"\1\n        }\n\n        function showStep",
        content
    )
    
    # Fix: missing } for showStep (after progressSteps.forEach block)
    content = re.sub(
        r"(pStep\.classList\.toggle\('active', index <= stepIndex\);\s*\n\s*\}\);\s*\n)\s*\n\s*function validateStep",
        r"\1        }\n\n        function validateStep",
        content
    )
    
    # Fix mobile menu script - the doubled pattern
    content = re.sub(MOBILE_DOUBLED_PATTERN, MOBILE_DOUBLED_FIXED, content)
    
    # Fix: comment that becomes a regex / instead of //
    content = content.replace(
        "        / ==================== MULTI-STEP FORM LOGIC ====================",
        "        // ==================== MULTI-STEP FORM LOGIC ===================="
    )
    
    if content != orig:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {os.path.basename(filepath)}")
    else:
        print(f"No change: {os.path.basename(filepath)}")

