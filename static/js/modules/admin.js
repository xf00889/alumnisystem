/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--admin-accounts-mentor-remove-mentors-form-html") && !executed["admin/accounts/mentor/remove_mentors_form.html"]) {
executed["admin/accounts/mentor/remove_mentors_form.html"] = true;
/* BEGIN: admin/accounts/mentor/remove_mentors_form.html */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('remove-mentors-form');
    const reasonField = document.getElementById('removal_reason');
    
    form.addEventListener('submit', function(e) {
        const reason = reasonField.value.trim();
        
        if (!reason) {
            e.preventDefault();
            alert('Please provide a disable reason.');
            reasonField.focus();
            return false;
        }
        
        if (!confirm('Are you sure you want to disable the selected mentor(s)? This action cannot be undone.')) {
            e.preventDefault();
            return false;
        }
    });
});

/* END: admin/accounts/mentor/remove_mentors_form.html */
}
if (document.documentElement.classList.contains("fe-page--admin-smtp-configuration-form-html") && !executed["admin/smtp_configuration_form.html"]) {
executed["admin/smtp_configuration_form.html"] = true;
/* BEGIN: admin/smtp_configuration_form.html */

document.addEventListener('DOMContentLoaded', function() {
    const predefinedConfigs = document.querySelectorAll('.predefined-config');
    const form = document.getElementById('smtpForm');
    
    // Predefined configuration templates
    const configTemplates = {
        'gmail': {
            name: 'Gmail',
            host: 'smtp.gmail.com',
            port: 587,
            use_tls: true,
            use_ssl: false
        },
        'outlook': {
            name: 'Outlook',
            host: 'smtp-mail.outlook.com',
            port: 587,
            use_tls: true,
            use_ssl: false
        },
        'yahoo': {
            name: 'Yahoo',
            host: 'smtp.mail.yahoo.com',
            port: 587,
            use_tls: true,
            use_ssl: false
        },
        'custom': {
            name: 'Custom SMTP',
            host: '',
            port: 587,
            use_tls: true,
            use_ssl: false
        }
    };
    
    // Handle predefined configuration selection
    predefinedConfigs.forEach(config => {
        config.addEventListener('click', function() {
            const configKey = this.dataset.config;
            const template = configTemplates[configKey];
            
            if (template) {
                // Remove selected class from all configs
                predefinedConfigs.forEach(c => c.classList.remove('selected'));
                
                // Add selected class to clicked config
                this.classList.add('selected');
                
                // Fill form with template data
                document.getElementById('name').value = template.name;
                document.getElementById('host').value = template.host;
                document.getElementById('port').value = template.port;
                document.getElementById('use_tls').checked = template.use_tls;
                document.getElementById('use_ssl').checked = template.use_ssl;
                
                // Focus on username field
                document.getElementById('username').focus();
            }
        });
    });
    
    // Handle TLS/SSL mutual exclusivity
    const useTlsCheckbox = document.getElementById('use_tls');
    const useSslCheckbox = document.getElementById('use_ssl');
    
    useTlsCheckbox.addEventListener('change', function() {
        if (this.checked) {
            useSslCheckbox.checked = false;
        }
    });
    
    useSslCheckbox.addEventListener('change', function() {
        if (this.checked) {
            useTlsCheckbox.checked = false;
        }
    });
    
    // Auto-update port based on encryption
    useTlsCheckbox.addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('port').value = 587;
        }
    });
    
    useSslCheckbox.addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('port').value = 465;
        }
    });
    
    // Form validation
    form.addEventListener('submit', function(e) {
        const useTls = useTlsCheckbox.checked;
        const useSsl = useSslCheckbox.checked;
        const port = parseInt(document.getElementById('port').value);
        
        // Validate TLS/SSL combination
        if (useTls && useSsl) {
            e.preventDefault();
            alert('Cannot use both TLS and SSL. Please choose one encryption method.');
            return;
        }
        
        // Validate port and encryption combination
        if (port === 465 && !useSsl) {
            e.preventDefault();
            alert('Port 465 requires SSL encryption. Please enable SSL or use port 587 with TLS.');
            return;
        }
        
        if (port === 587 && !useTls) {
            e.preventDefault();
            alert('Port 587 requires TLS encryption. Please enable TLS or use port 465 with SSL.');
            return;
        }
    });
});

/* END: admin/smtp_configuration_form.html */
}
if (document.documentElement.classList.contains("fe-page--admin-user-management-user-create-html") && !executed["admin/user_management/user_create.html"]) {
executed["admin/user_management/user_create.html"] = true;
/* BEGIN: admin/user_management/user_create.html */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('userCreateForm');
    const submitBtn = document.getElementById('submitBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const passwordInput = document.getElementById('id_password');
    const passwordConfirmInput = document.getElementById('id_password_confirm');
    const passwordStrength = document.getElementById('passwordStrength');
    const strengthBarFill = document.getElementById('strengthBarFill');
    const strengthText = document.getElementById('strengthText');

    // Password strength checker
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            
            if (password.length === 0) {
                passwordStrength.style.display = 'none';
                return;
            }

            passwordStrength.style.display = 'block';

            // Check requirements
            const requirements = {
                length: password.length >= 8,
                uppercase: /[A-Z]/.test(password),
                lowercase: /[a-z]/.test(password),
                number: /[0-9]/.test(password)
            };

            // Update requirement indicators
            document.getElementById('req-length').classList.toggle('met', requirements.length);
            document.getElementById('req-uppercase').classList.toggle('met', requirements.uppercase);
            document.getElementById('req-lowercase').classList.toggle('met', requirements.lowercase);
            document.getElementById('req-number').classList.toggle('met', requirements.number);

            // Calculate strength
            const metCount = Object.values(requirements).filter(Boolean).length;
            
            strengthBarFill.className = 'strength-bar-fill';
            if (metCount <= 2) {
                strengthBarFill.classList.add('strength-weak');
                strengthText.textContent = 'Weak';
                strengthText.style.color = 'var(--feedback-error)';
            } else if (metCount === 3) {
                strengthBarFill.classList.add('strength-medium');
                strengthText.textContent = 'Medium';
                strengthText.style.color = 'var(--feedback-warning)';
            } else {
                strengthBarFill.classList.add('strength-strong');
                strengthText.textContent = 'Strong';
                strengthText.style.color = 'var(--feedback-success)';
            }
        });
    }

    // Form submission with loading indicator
    form.addEventListener('submit', function(e) {
        // Basic client-side validation
        let isValid = true;
        const email = document.getElementById('id_email').value.trim();
        const firstName = document.getElementById('id_first_name').value.trim();
        const lastName = document.getElementById('id_last_name').value.trim();
        const password = passwordInput.value;
        const passwordConfirm = passwordConfirmInput.value;

        if (!email || !firstName || !lastName || !password || !passwordConfirm) {
            e.preventDefault();
            alert('Please fill in all required fields');
            return;
        }

        if (password !== passwordConfirm) {
            e.preventDefault();
            alert('Passwords do not match');
            passwordConfirmInput.focus();
            return;
        }

        if (password.length < 8) {
            e.preventDefault();
            alert('Password must be at least 8 characters long');
            passwordInput.focus();
            return;
        }

        // Show loading overlay
        loadingOverlay.classList.add('show');
        submitBtn.disabled = true;
        submitBtn.classList.add('btn-loading');
    });
});

/* END: admin/user_management/user_create.html */
}
if (document.documentElement.classList.contains("fe-page--admin-user-management-user-list-html") && !executed["admin/user_management/user_list.html"]) {
executed["admin/user_management/user_list.html"] = true;
/* BEGIN: admin/user_management/user_list.html */

// Handle sortable table headers
document.addEventListener('DOMContentLoaded', function() {
    const sortableHeaders = document.querySelectorAll('.sortable-header');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortField = this.dataset.sort;
            const currentSort = new URLSearchParams(window.location.search).get('sort');
            
            // Determine new sort direction
            let newSort = sortField;
            if (currentSort === sortField) {
                // Toggle to descending
                newSort = '-' + sortField;
            } else if (currentSort === '-' + sortField) {
                // Remove sort (back to default)
                newSort = '';
            }
            
            // Build new URL with sort parameter
            const url = new URL(window.location);
            if (newSort) {
                url.searchParams.set('sort', newSort);
            } else {
                url.searchParams.delete('sort');
            }
            
            // Navigate to new URL
            window.location.href = url.toString();
        });
    });
});

/* END: admin/user_management/user_list.html */
}
})();
