/**
 * School Management ERP - Main JavaScript (Sprint 0)
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const sidebar = document.getElementById('appSidebar');
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
            if (sidebarBackdrop) {
                sidebarBackdrop.classList.toggle('active');
            }
        });
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', () => {
            sidebar.classList.remove('mobile-open');
            sidebarBackdrop.classList.remove('active');
        });
    }

    // 2. Password Show / Hide Toggle
    const togglePasswordButtons = document.querySelectorAll('.password-toggle-btn');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetInputId = button.getAttribute('data-target') || 'id_password';
            const passwordInput = document.getElementById(targetInputId);
            if (passwordInput) {
                const isPassword = passwordInput.getAttribute('type') === 'password';
                passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
                button.textContent = isPassword ? '🔒 Hide' : '👁️ Show';
            }
        });
    });

    // 3. Quick Role Credentials Autofill on Login Page
    const roleFillButtons = document.querySelectorAll('.role-fill-btn');
    const usernameInput = document.getElementById('id_username');
    const passwordInput = document.getElementById('id_password');

    roleFillButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const role = btn.getAttribute('data-role');
            if (usernameInput && passwordInput) {
                usernameInput.value = role;
                passwordInput.value = `${role}123`;
                // Add a brief visual pulse
                btn.style.borderColor = 'var(--primary)';
                setTimeout(() => {
                    btn.style.borderColor = '';
                }, 300);
            }
        });
    });

    // 4. Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // 5. Dark Mode Persistent Theme Initializer
    const currentTheme = localStorage.getItem('school_erp_theme') || 'light';
    if (currentTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        const themeBtn = document.getElementById('themeToggleBtn');
        if (themeBtn) themeBtn.textContent = '☀️';
    }
});

// Global Theme Toggle
function toggleTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    if (newTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('school_erp_theme', newTheme);
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
        themeBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    }
}

