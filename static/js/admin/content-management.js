/* Shared protected admin directory interactions; no global app navigation changes. */
(() => {
  'use strict';
  const modal = document.getElementById('staffContentDialog');
  let previousFocus = null;
  if (modal) {
    const body = modal.querySelector('[data-modal-body]');
    const title = document.getElementById('staffContentDialogTitle');
    document.addEventListener('click', async (event) => {
      const trigger = event.target.closest('[data-modal-url]');
      if (!trigger) return;
      event.preventDefault();
      previousFocus = trigger;
      title.textContent = trigger.dataset.modalTitle || 'Details';
      body.textContent = 'Loading details…';
      if (!modal.open) modal.showModal();
      try {
        const result = await fetch(trigger.dataset.modalUrl, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin', cache: 'no-store'
        });
        if (!result.ok) throw new Error('Unable to load details (' + result.status + ').');
        // Same-origin HTML from our permission-checked Django template.
        body.innerHTML = await result.text();
      } catch (error) {
        body.textContent = error.message || 'Unable to load details.';
      }
    });
    modal.querySelector('[data-modal-close]').addEventListener('click', () => modal.close());
    modal.addEventListener('click', (event) => { if (event.target === modal) modal.close(); });
    modal.addEventListener('close', () => { if (previousFocus) previousFocus.focus(); });
  }

  // A previously stored image may no longer exist on external media storage.
  // Avoid showing the browser's broken-image icon when that happens.
  document.querySelectorAll('.staff-content-form .preview-image, .staff-content-form .staff-form-image-preview').forEach((img) => {
    const hideBroken = () => {
      img.hidden = true;
      if (img.nextElementSibling?.classList.contains('upload-image-missing')) return;
      const hint = document.createElement('p');
      hint.className = 'upload-image-missing text-muted small';
      hint.textContent = 'Image preview unavailable. Choose an image to replace it.';
      img.insertAdjacentElement('afterend', hint);
    };
    img.addEventListener('error', hideBroken, {once:true});
    if (img.complete && img.naturalWidth === 0) hideBroken();
  });

  document.querySelectorAll('form[data-confirm-submit], form[data-confirm-delete]').forEach((form) => {
    let confirmed = false;
    form.addEventListener('submit', async (event) => {
      if (confirmed) return;
      event.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const isDelete = form.hasAttribute('data-confirm-delete');
      const title = isDelete ? 'Delete ' + (form.dataset.deleteName || 'this item') + '?' : (form.dataset.confirmTitle || 'Save changes?');
      const message = isDelete ? 'This action cannot be undone.' : (form.dataset.confirmText || 'Please verify the information before saving.');
      if (window.Swal?.fire) {
        const result = await window.Swal.fire({title, text:message, icon:isDelete?'warning':'question',
          showCancelButton:true, confirmButtonText:isDelete?'Delete':'Confirm', confirmButtonColor:isDelete?'#b73542':'#243d70'});
        if (!result.isConfirmed) return;
      } else if (!window.confirm(title + '\n' + message)) return;
      confirmed = true;
      form.requestSubmit(event.submitter || undefined);
    });
  });

  document.querySelectorAll('[data-export-table]').forEach((button) => button.addEventListener('click', () => {
    const table = document.getElementById(button.dataset.exportTable);
    if (!table) return;
    const lines = Array.from(table.rows).map((row) => Array.from(row.cells).slice(0,-1).map((cell) =>
      '"' + cell.innerText.trim().replace(/"/g, '""') + '"').join(','));
    const blob = new Blob(['\uFEFF' + lines.join('\r\n')], {type:'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
    anchor.href=url; anchor.download='norsu-events-visible-page.csv'; document.body.append(anchor);anchor.click();anchor.remove();
    URL.revokeObjectURL(url);
  }));
})();
