/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
// The create-phase1 and progressive pages intentionally share one initializer.
if ((document.documentElement.classList.contains("fe-page--alumni-groups-group-create-phase1-html") || document.documentElement.classList.contains("fe-page--alumni-groups-group-create-progressive-html")) && !executed["alumni-groups:create-batch-years"]) {
executed["alumni-groups:create-batch-years"] = true;
/* BEGIN SHARED: alumni_groups/group_create_phase1.html + alumni_groups/group_create_progressive.html */

document.addEventListener('DOMContentLoaded', function() {
    // Django messages are now processed automatically by base.html
    // No need to manually call processDjangoMessages() here
    // The ToastUtils.processDjangoMessages() function runs globally on page load
    
    // Form validation
    const form = document.querySelector('form');
    const batchStartYear = document.getElementById('batch_start_year');
    const batchEndYear = document.getElementById('batch_end_year');
    
    form.addEventListener('submit', function(e) {
        const startYear = parseInt(batchStartYear.value);
        const endYear = parseInt(batchEndYear.value);
        
        if (startYear && endYear && startYear > endYear) {
            e.preventDefault();
            Swal.fire({
                title: 'Invalid Year Range',
                text: 'Start year must be less than or equal to end year.',
                icon: 'error',
                confirmButtonColor: '#2b3c6b'
            });
        }
    });
});

/* END SHARED: creation form validation */
}
if (document.documentElement.classList.contains("fe-page--alumni-groups-manage-members-html") && !executed["alumni_groups/manage_members.html"]) {
executed["alumni_groups/manage_members.html"] = true;
/* BEGIN: alumni_groups/manage_members.html */

document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const answersModal = new bootstrap.Modal(document.getElementById('securityAnswersModal'));

    const requestedTab = new URLSearchParams(window.location.search).get('tab');
    if (requestedTab) {
        const trigger = document.querySelector(`[data-bs-target="#${requestedTab}"]`);
        if (trigger && window.bootstrap?.Tab) {
            bootstrap.Tab.getOrCreateInstance(trigger).show();
        }
    }

    // Confirm member actions using the same-page Bootstrap modal (never native confirm).
    const memberActionModalEl = document.getElementById('groupMemberActionModal');
    const memberActionModal = memberActionModalEl ? bootstrap.Modal.getOrCreateInstance(memberActionModalEl) : null;
    const memberActionTitle = document.getElementById('groupMemberActionTitle');
    const memberActionDescription = document.getElementById('groupMemberActionDescription');
    const memberActionError = document.getElementById('groupMemberActionError');
    const memberActionConfirm = document.getElementById('groupMemberActionConfirm');
    let pendingMemberAction = null;

    document.querySelectorAll('.member-action').forEach(button => {
        button.addEventListener('click', function () {
            pendingMemberAction = { action: this.dataset.action, membershipId: this.dataset.membershipId };
            const memberName = this.closest('.member-grid-item')?.querySelector('.member-grid-name')?.textContent?.trim() || 'this member';
            const labels = {
                approve: 'Approve member', reject: 'Reject join request', remove: 'Remove member',
                promote: 'Make group administrator', demote: 'Change to member',
                make_moderator: 'Assign moderator role', reinstate: 'Reinstate member'
            };
            memberActionTitle.textContent = labels[pendingMemberAction.action] || 'Confirm member action';
            memberActionDescription.textContent = `Apply “${labels[pendingMemberAction.action] || pendingMemberAction.action}” to ${memberName}?`;
            memberActionError.hidden = true;
            memberActionError.textContent = '';
            memberActionConfirm.disabled = false;
            memberActionConfirm.textContent = 'Confirm action';
            memberActionConfirm.className = 'btn ' + (['remove', 'reject'].includes(pendingMemberAction.action) ? 'btn-danger' : 'btn-primary');
            memberActionModal?.show();
        });
    });

    memberActionConfirm?.addEventListener('click', async function () {
        if (!pendingMemberAction) return;
        this.disabled = true;
        this.textContent = 'Saving...';
        try {
            const response = await fetch(`/groups/api/member/${pendingMemberAction.membershipId}/status/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ action: pendingMemberAction.action }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(payload.message || payload.error || 'Unable to update this member.');
            memberActionModal.hide();
            window.location.reload();
        } catch (error) {
            memberActionError.textContent = error.message || 'Unable to update this member.';
            memberActionError.hidden = false;
            this.disabled = false;
            this.textContent = 'Try again';
        }
    });

    // Handle viewing security answers
    document.querySelectorAll('.view-answers').forEach(button => {
        button.addEventListener('click', async function() {
            const membershipId = this.dataset.membershipId;

            try {
                const response = await fetch(`/groups/api/member/${membershipId}/security-answers/`);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to load security answers');
                }

                const container = document.getElementById('securityAnswersContent');
                container.replaceChildren();
                if (!(data.answers || []).length) {
                    const notice = document.createElement('p');
                    notice.className = 'alert alert-warning mb-0';
                    notice.textContent = data.message || 'No membership question answers were submitted.';
                    container.appendChild(notice);
                }
                if (data.missing_required && (data.answers || []).length) {
                    const notice = document.createElement('p');
                    notice.className = 'alert alert-warning';
                    notice.textContent = data.message || 'Some required membership answers are still missing.';
                    container.appendChild(notice);
                }
                (data.answers || []).forEach(answer => {
                    const row = document.createElement('div');
                    row.className = 'answer-item';
                    const parts = String(answer).split('\n');
                    const heading = document.createElement('div');
                    heading.className = 'fw-bold mb-1';
                    heading.textContent = parts.shift() || '';
                    const detail = document.createElement('div');
                    detail.textContent = parts.join('\n');
                    row.append(heading, detail);
                    container.appendChild(row);
                });
                answersModal.show();
            } catch (error) {
                console.error('Error:', error);
                alert(error.message || 'Failed to load security answers');
            }
        });
    });

    // Handle post approval/rejection
    document.querySelectorAll('.approve-post, .reject-post').forEach(button => {
        button.addEventListener('click', async function() {
            if (!await window.NORSUGroupConfirm('Do you want to ' + this.dataset.action + ' this group post?', this.dataset.action === 'reject')) {
                return;
            }

            const postId = this.dataset.postId;
            const action = this.dataset.action;

            try {
                const formData = new FormData();
                formData.append('action', action);
                const csrfToken = window.NORSUAlumni?.csrf?.getToken() ||
                    document.querySelector('[name="csrfmiddlewaretoken"]')?.value;
                if (!csrfToken) {
                    alert('Your security token is unavailable. Refresh the page and try again.');
                    return;
                }
                formData.append('csrfmiddlewaretoken', csrfToken);

                const response = await fetch(`/groups/api/post/${postId}/approve/`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    // Remove the post from pending and add to appropriate tab
                    const postElement = document.getElementById(`post-${postId}`);
                    postElement.remove();

                    // Refresh the page to update counts and lists
                    window.location.reload();
                } else {
                    const errorData = await response.json();
                    alert(errorData.error || 'Failed to process post. Please try again.');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    });


    const reviewModal = document.getElementById('reportReviewModal');
    if (reviewModal) {
        const reviewForm = document.getElementById('reportReviewForm');
        const reviewAction = document.getElementById('reportReviewAction');
        const reviewTitle = document.getElementById('reportReviewModalLabel');
        const reviewDescription = document.getElementById('reportReviewModalDescription');
        const reviewNote = document.getElementById('reportReviewNote');
        const reviewNoteLabel = document.getElementById('reportReviewNoteLabel');
        const reviewNoteHelp = document.getElementById('reportReviewNoteHelp');
        const reviewSubmit = document.getElementById('reportReviewSubmit');

        reviewModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget;
            if (!trigger) return;
            const action = trigger.getAttribute('data-review-action') || 'resolve';
            const title = trigger.getAttribute('data-review-title') || 'Review report';
            const description = trigger.getAttribute('data-review-description') || '';
            const requiresNote = trigger.getAttribute('data-review-requires-note') === 'true';

            reviewForm.action = trigger.getAttribute('data-report-action') || reviewForm.action;
            reviewAction.value = action;
            reviewTitle.textContent = title;
            reviewDescription.textContent = description;
            reviewNote.value = '';
            reviewNote.required = requiresNote;
            reviewNoteLabel.textContent = requiresNote ? 'Reason for rejecting the report' : 'Moderator note';
            reviewNote.placeholder = requiresNote ? 'Explain why this report is being rejected' : 'Optional note for this moderation action';
            reviewNoteHelp.textContent = requiresNote
                ? 'A short note is required when rejecting a report.'
                : 'This note is stored with the moderation review.';
            reviewSubmit.className = 'btn ' + (action === 'remove_post' ? 'btn-danger' : 'btn-primary');
            reviewSubmit.textContent = action === 'dismiss'
                ? 'Reject report'
                : (action === 'remove_post' ? 'Approve & remove post' : 'Approve report');
        });
    }
});

/* END: alumni_groups/manage_members.html */
}
})();
