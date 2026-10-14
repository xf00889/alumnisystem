/* Admin-only group summary and status controls; all mutations remain server validated. */
(function () {
    'use strict';
    const summary = document.getElementById('adminGroupSummaryModal');
    if (summary) {
        summary.addEventListener('show.bs.modal', (event) => {
            const trigger = event.relatedTarget;
            if (!trigger) return;
            const fields = {
                'adminGroupSummaryName': 'name',
                'adminGroupSummaryBatch': 'batch',
                'adminGroupSummaryAdmin': 'admin',
                'adminGroupSummaryMembers': 'count',
                'adminGroupSummaryType': 'type',
                'adminGroupSummaryCreated': 'created',
                'adminGroupSummaryStatus': 'status',
                'adminGroupSummaryReason': 'reason'
            };
            Object.entries(fields).forEach(([id, key]) => {
                const node = document.getElementById(id);
                if (node) node.textContent = trigger.dataset[key] || 'Not provided';
            });
        });
    }
    const statusModal = document.getElementById('adminGroupStatusModal');
    if (statusModal) {
        statusModal.addEventListener('show.bs.modal', (event) => {
            const trigger = event.relatedTarget;
            if (!trigger) return;
            const form = document.getElementById('adminGroupStatusForm');
            const action = trigger.dataset.statusAction === 'enable' ? 'enable' : 'disable';
            const title = document.getElementById('adminGroupStatusTitle');
            const reason = document.getElementById('adminGroupStatusReason');
            const submit = document.getElementById('adminGroupStatusSubmit');
            form.action = trigger.dataset.statusUrl;
            form.elements.namedItem('action').value = action;
            title.textContent = `${action === 'disable' ? 'Disable' : 'Re-enable'} ${trigger.dataset.groupName || 'group'}?`;
            reason.required = action === 'disable';
            reason.value = '';
            reason.closest('.mb-3').hidden = action === 'enable';
            submit.textContent = action === 'disable' ? 'Disable group' : 'Re-enable group';
            submit.className = action === 'disable' ? 'btn btn-danger' : 'btn btn-success';
        });
    }
})();
