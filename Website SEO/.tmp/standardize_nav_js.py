import os
import re

def standardize_script(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r') as f:
        content = f.read()

    # Unified Script for Navigation
    unified_nav_script = """
    <script>
        // FIXED: MOBILE MENU TOGGLE (Unified System)
        document.addEventListener('DOMContentLoaded', function() {
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
        });
    </script>
    """

    # Cleanup the literal \n and any other duplicates
    content = content.replace('\\n</body>', '</body>')
    content = re.sub(r'<script>\s+// FIXED: MOBILE MENU TOGGLE.*?// FIXED: MOBILE MENU TOGGLE', '<script>\\n        // FIXED: MOBILE MENU TOGGLE', content, flags=re.DOTALL)
    
    # Ensure it's there
    if 'FIXED: MOBILE MENU TOGGLE' not in content:
        if '</body>' in content:
            content = content.replace('</body>', f'{unified_nav_script}\n</body>')
    
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Polished Script in {file_path}")

# Run for all pages
pages = [
    'public_html/index.html',
    'public_html/en.html',
    'public_html/services.html',
    'public_html/services-en.html',
    'public_html/process.html',
    'public_html/process-en.html',
    'public_html/contact.html',
    'public_html/contact-en.html',
    'public_html/about.html',
    'public_html/about-en.html',
    'public_html/blog.html',
    'public_html/blog_ar.html'
]

for page in pages:
    standardize_script(page)
