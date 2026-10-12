/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--smtp-configuration-form-html") && !executed["smtp_configuration_form.html"]) {
executed["smtp_configuration_form.html"] = true;
/* BEGIN: smtp_configuration_form.html */

document.addEventListener('DOMContentLoaded', function() {
    const providerCards = document.querySelectorAll('.provider-card');
    const providerSelection = document.getElementById('provider-selection');
    const configurationForm = document.getElementById('configuration-form');
    const backToProviderBtn = document.getElementById('back-to-provider');
    
    const stepProvider = document.getElementById('step-provider');
    const stepDetails = document.getElementById('step-details');
    const stepTest = document.getElementById('step-test');
    
    // Provider configurations
    const providerConfigs = {
        gmail: {
            name: 'Gmail Configuration',
            host: 'smtp.gmail.com',
            port: 587,
            use_tls: true,
            use_ssl: false,
            passwordHelp: 'Use App Password (not your regular password). Enable 2FA and create App Password in Google Account settings.'
        },
        outlook: {
            name: 'Outlook Configuration',
            host: 'smtp-mail.outlook.com',
            port: 587,
            use_tls: true,
            use_ssl: false,
            passwordHelp: 'Use your regular Outlook/Hotmail password.'
        },
        yahoo: {
            name: 'Yahoo Configuration',
            host: 'smtp.mail.yahoo.com',
            port: 587,
            use_tls: true,
            use_ssl: false,
            passwordHelp: 'Use App Password (not your regular password). Enable 2FA and create App Password in Yahoo Account settings.'
        },
        custom: {
            name: 'Custom SMTP Configuration',
            host: '',
            port: 587,
            use_tls: true,
            use_ssl: false,
            passwordHelp: 'Contact your email provider for the correct password.'
        }
    };
    
    // Handle provider selection
    providerCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove selected class from all cards
            providerCards.forEach(c => c.classList.remove('selected'));
            
            // Add selected class to clicked card
            this.classList.add('selected');
            
            // Get provider type
            const provider = this.dataset.provider;
            const config = providerConfigs[provider];
            
            // Fill form with provider configuration
            document.getElementById('name').value = config.name;
            document.getElementById('host').value = config.host;
            document.getElementById('port').value = config.port;
            document.getElementById('use_tls').checked = config.use_tls;
            document.getElementById('use_ssl').checked = config.use_ssl;
            document.getElementById('password-help').textContent = config.passwordHelp;
            
            // Auto-fill username with from_email if it's empty
            const fromEmail = document.getElementById('from_email').value;
            const username = document.getElementById('username');
            if (!username.value && fromEmail) {
                username.value = fromEmail;
            }
            
            // Show configuration form
            providerSelection.classList.add('hidden');
            configurationForm.classList.remove('hidden');
            
            // Update step indicator
            stepProvider.classList.remove('active');
            stepProvider.classList.add('completed');
            stepDetails.classList.remove('pending');
            stepDetails.classList.add('active');
        });
    });
    
    // Handle back to provider selection
    backToProviderBtn.addEventListener('click', function() {
        configurationForm.classList.add('hidden');
        providerSelection.classList.remove('hidden');
        
        // Update step indicator
        stepProvider.classList.add('active');
        stepProvider.classList.remove('completed');
        stepDetails.classList.remove('active');
        stepDetails.classList.add('pending');
    });
    
    // Handle TLS/SSL mutual exclusivity
    const tlsCheckbox = document.getElementById('use_tls');
    const sslCheckbox = document.getElementById('use_ssl');
    const portInput = document.getElementById('port');
    
    if (tlsCheckbox && sslCheckbox && portInput) {
        tlsCheckbox.addEventListener('change', function() {
            if (this.checked) {
                sslCheckbox.checked = false;
                portInput.value = '587';
            }
        });
        
        sslCheckbox.addEventListener('change', function() {
            if (this.checked) {
                tlsCheckbox.checked = false;
                portInput.value = '465';
            }
        });
    }
    
    // Auto-fill username when from_email changes
    const fromEmailInput = document.getElementById('from_email');
    const usernameInput = document.getElementById('username');
    
    fromEmailInput.addEventListener('input', function() {
        if (!usernameInput.value) {
            usernameInput.value = this.value;
        }
    });
    
    // Handle form submission - update step indicator
    const smtpForm = document.getElementById('smtp-form');
    if (smtpForm) {
        smtpForm.addEventListener('submit', function() {
            // Update step indicator to show we're in the test/save phase
            stepDetails.classList.remove('active');
            stepDetails.classList.add('completed');
            stepTest.classList.remove('pending');
            stepTest.classList.add('active');
        });
    }
});

/* END: smtp_configuration_form.html */
}
})();
