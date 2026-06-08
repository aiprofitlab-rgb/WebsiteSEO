(async () => {

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
    
})();