<script>
console.log('=== Group Chat Script Loading ===');

// Enhanced Group Chat Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== Group Chat DOMContentLoaded ===');
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-resize textarea
    const messageInput = document.querySelector('.message-input');
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Handle Enter key for sending messages
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const form = this.closest('form');
                if (form && this.value.trim()) {
                    form.dispatchEvent(new Event('submit'));
                }
            }
        });
    }

    // Smooth scroll to bottom when new messages arrive
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        const scrollToBottom = () => {
            const scrollArea = messagesContainer.querySelector('.messages-scroll-area');
            if (scrollArea) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
        };

        // Scroll to bottom on load
        setTimeout(scrollToBottom, 100);

        // Observe for new messages
        const observer = new MutationObserver(scrollToBottom);
        observer.observe(messagesContainer, { childList: true, subtree: true });
    }

    // Enhanced file attachment handling
    const attachmentInput = document.getElementById('groupAttachmentInput');
    const attachmentBtn = document.querySelector('.attachment-btn');

    if (attachmentInput && attachmentBtn) {
        attachmentInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Show file preview or name
                const fileName = file.name;
                const fileSize = (file.size / 1024 / 1024).toFixed(2);

                // Update button to show file selected
                attachmentBtn.innerHTML = '<i class="fas fa-check"></i>';
                attachmentBtn.style.background = 'var(--feedback-success)';
                attachmentBtn.style.color = 'white';

                // Show tooltip with file info
                attachmentBtn.setAttribute('title', `${fileName} (${fileSize}MB)`);

                // Reset after 3 seconds
                setTimeout(() => {
                    attachmentBtn.innerHTML = '<i class="fas fa-paperclip"></i>';
                    attachmentBtn.style.background = '';
                    attachmentBtn.style.color = '';
                    attachmentBtn.setAttribute('title', 'Attach file');
                }, 3000);
            }
        });
    }
});

// Group message sending function - using proven direct message pattern
function sendGroupMessage(event, conversationId) {
    console.log('=== sendGroupMessage called ===');
    console.log('Event:', event);
    console.log('Conversation ID:', conversationId);

    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = form.querySelector('.message-input');
    const submitBtn = form.querySelector('.send-btn');

    // Validate input
    if (!messageInput || !messageInput.value.trim()) {
        if (messageInput) messageInput.focus();
        return;
    }

    // Show loading state
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    fetch(`/connections/send-group-message/${conversationId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add the new message to the container (same as direct messages)
            const scrollArea = messagesContainer.querySelector('.messages-scroll-area');
            if (scrollArea && data.message_html) {
                scrollArea.insertAdjacentHTML('beforeend', data.message_html);
            }

            // Clear the form
            form.reset();
            if (messageInput) {
                messageInput.style.height = 'auto';
            }

            // Scroll to bottom
            if (scrollArea) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
        } else {
            console.error('Error sending message:', data.error || data.message);
            alert('Error sending message: ' + (data.error || data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error sending message. Please try again.');
    })
    .finally(() => {
        // Re-enable submit button
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    });
}

</script>