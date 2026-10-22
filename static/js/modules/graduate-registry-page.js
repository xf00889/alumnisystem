/** Graduate Registry comparison: only changed/new records are shown; no writes before confirmation. */
(function () {
  'use strict';
  const form = document.getElementById('grImportForm');
  if (!form) return;
  const find = (id) => document.getElementById(id);
  const file = find('grImportFile');
  const campus = find('grImportCampus');
  const year = find('grImportYear');
  const compare = find('grCompareButton');
  const download = find('grExportComparison');
  const commit = find('grCommitButton');
  const consent = find('grConfirmCheckbox');
  const status = find('grImportStatus');
  const result = find('grComparison');
  const summary = find('grComparisonMetrics');
  const rows = find('grComparisonRows');
  const hint = find('grComparisonHint');
  const details = find('registry-compare');
  const busyDialog = find('grBusyDialog');
  const feedbackDialog = find('grFeedbackDialog');
  const confirmDialog = find('grConfirmDialog');
  const confirmCancel = find('grConfirmCancel');
  const confirmProceed = find('grConfirmProceed');
  const tabDifferences = find('grTabDifferences');
  const tabNew = find('grTabNew');
  const tablePanel = find('grComparisonTablePanel');
  let inFlight = false;
  let checked = false;
  let imported = false;
  let comparison = null;
  let activeCategory = 'differences';

  find('grJumpToCompare')?.addEventListener('click', () => { details.open = true; });
  function showDialog(dialog) {
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  }
  function closeDialog(dialog) {
    if (typeof dialog.close === 'function') dialog.close();
    else dialog.removeAttribute('open');
  }
  // In-progress operations should not be dismissed accidentally.
  busyDialog.addEventListener('cancel', (event) => event.preventDefault());
  confirmCancel.addEventListener('click', () => closeDialog(confirmDialog));
  confirmDialog.addEventListener('click', (event) => {
    if (event.target === confirmDialog) closeDialog(confirmDialog);
  });
  const feedbackDone = find('grFeedbackDone');
  feedbackDone.addEventListener('click', () => closeDialog(feedbackDialog));
  feedbackDialog.addEventListener('click', (event) => {
    if (event.target === feedbackDialog) closeDialog(feedbackDialog);
  });

  function feedback(title, message, {error=false, refresh=false}={}) {
    find('grFeedbackTitle').textContent = title;
    find('grFeedbackMessage').textContent = message;
    find('grFeedbackIcon').classList.toggle('gr-dialog__result-icon--error', error);
    find('grFeedbackIcon').innerHTML = error
      ? '<i class="fas fa-exclamation-triangle" aria-hidden="true"></i>'
      : '<i class="fas fa-check" aria-hidden="true"></i>';
    find('grFeedbackRefresh').hidden = !refresh;
    if (!feedbackDialog.open) showDialog(feedbackDialog);
    feedbackDone.focus();
  }
  function note(message, type='info') {
    status.hidden = false;
    status.dataset.type = type;
    status.textContent = message;
  }
  function setBusy(busy, title, message) {
    inFlight = busy;
    compare.disabled = busy;
    download.disabled = busy || !checked;
    commit.disabled = busy || !checked || !consent.checked || imported || !hasImportable();
    file.disabled = busy; campus.disabled = busy; year.disabled = busy;
    if (busy) {
      find('grBusyTitle').textContent = title;
      find('grBusyMessage').textContent = message;
      if (!busyDialog.open) showDialog(busyDialog);
    } else if (busyDialog.open) closeDialog(busyDialog);
  }
  function invalidate() {
    checked = false; imported = false; comparison = null;
    consent.checked = false;
    commit.disabled = true;
    commit.innerHTML = '<i class="fas fa-file-import" aria-hidden="true"></i> Import eligible records';
    download.disabled = true;
    result.hidden = true;
    status.hidden = true;
  }
  [file, campus, year].forEach((element) => element.addEventListener('change', invalidate));
  year.addEventListener('input', invalidate);
  consent.addEventListener('change', () => {
    commit.disabled = !checked || !consent.checked || inFlight || imported || !hasImportable();
  });
  function requestBody(extra={}) {
    // Take FormData BEFORE disabling controls so the uploaded file is included.
    const body = new FormData(form);
    Object.entries(extra).forEach(([key, value]) => body.set(key, value));
    return body;
  }
  async function post(url, body) {
    const token = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const response = await fetch(url, {
      method:'POST', body, credentials:'same-origin',
      headers:{'X-CSRFToken':token || '', 'Accept':'application/json', 'X-Requested-With':'XMLHttpRequest'},
    });
    const json = await response.json().catch(() => null);
    if (!response.ok || !json?.ok) throw new Error(json?.message || 'The request could not be completed.');
    return json;
  }
  const counts = [
    ['unchanged','Matches'], ['new','New graduates'], ['update','Updates'],
    ['review','Needs review'], ['skipped','Invalid / skipped'],
  ];
  function total(key) { return Number(comparison?.totals?.[key] || 0); }
  function hasImportable() { return total('new') + total('update') > 0; }
  function isDifference(item) { return item.status !== 'new' && item.status !== 'unchanged'; }
  function renderTab(category) {
    activeCategory = category;
    const differences = category === 'differences';
    tabDifferences.setAttribute('aria-selected', String(differences));
    tabNew.setAttribute('aria-selected', String(!differences));
    tablePanel.setAttribute('aria-labelledby', differences ? 'grTabDifferences' : 'grTabNew');
    rows.replaceChildren();
    const filtered = (comparison?.rows || []).filter((item) => differences ? isDifference(item) : item.status === 'new');
    filtered.forEach((item) => {
      const tr = document.createElement('tr');
      ['source','name','year','campus','course'].forEach((key) => {
        const cell = document.createElement('td'); cell.textContent = String(item[key] || '—'); tr.appendChild(cell);
      });
      const cell = document.createElement('td');
      const chip = document.createElement('span');
      chip.className = 'gr-pill gr-pill--' + (counts.some(([key]) => key === item.status) ? item.status : 'review');
      chip.textContent = ({new:'New',update:'Update',review:'Review',skipped:'Skipped'})[item.status] || 'Review';
      cell.appendChild(chip); tr.appendChild(cell);
      const reason = document.createElement('td'); reason.textContent = item.changes || '—'; tr.appendChild(reason);
      rows.appendChild(tr);
    });
    if (filtered.length === 0) {
      const tr = document.createElement('tr');
      const cell = document.createElement('td'); cell.colSpan = 7;
      cell.className = 'gr-table-empty';
      cell.textContent = differences ? 'No changed or conflicting records in this comparison.' : 'No new graduates in this comparison.';
      tr.appendChild(cell); rows.appendChild(tr);
    }
  }
  tabDifferences.addEventListener('click', () => renderTab('differences'));
  tabNew.addEventListener('click', () => renderTab('new'));
  function renderComparison(data) {
    comparison = data;
    summary.replaceChildren();
    counts.forEach(([key,label]) => {
      const card = document.createElement('div');
      const number = document.createElement('strong'); number.textContent = String(total(key));
      const caption = document.createElement('span'); caption.textContent = label;
      card.append(number,caption); summary.appendChild(card);
    });
    const differenceCount = total('update') + total('review') + total('skipped');
    find('grDifferenceCount').textContent = String(differenceCount);
    find('grNewCount').textContent = String(total('new'));
    renderTab(differenceCount ? 'differences' : 'new');
    const visibleCount = Number(data.total_rows || 0);
    const shownCount = Number(data.shown || 0);
    hint.textContent = `${total('unchanged')} already match and are hidden. ` +
      `${shownCount} of ${visibleCount} actionable rows shown. ` +
      (visibleCount > shownCount ? 'Download the comparison CSV to review all differences. ' : '') +
      'Comparing a partial registrar list does not label other registry entries as missing.';
    result.hidden = false;
    result.scrollIntoView({behavior:'smooth', block:'nearest'});
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (inFlight || !form.reportValidity()) return;
    if (!/\.(csv|xlsx)$/i.test(file.files?.[0]?.name || '')) return note('Choose a CSV or XLSX registrar file.','error');
    if (file.files[0].size > 10 * 1024 * 1024) return note('File exceeds the 10 MB limit.','error');
    const body = requestBody();
    checked = false; imported = false; comparison = null;
    result.hidden = true; consent.checked = false;
    let popup = null;
    setBusy(true, 'Comparing registrar file', 'Checking incoming graduates against the current registry…');
    try {
      const data = await post(form.dataset.compareUrl, body);
      comparison = data;
      checked = true;
      if (Number(data.totals?.unchanged || 0) > 0 &&
          ['new','update','review','skipped'].every((key) => Number(data.totals?.[key] || 0) === 0)) {
        checked = false; // No CSV or write action needed for a perfect match.
        result.hidden = true;
        status.hidden = true;
        popup = ['All records match', `All ${data.totals.unchanged} graduate records already match the registry. Nothing needs importing.`];
      } else {
        renderComparison(data);
        note('Comparison complete. Only new and differing records are displayed.', 'success');
      }
    } catch (error) {
      checked = false;
      note(error.message || 'Comparison failed; no changes were made.', 'error');
      popup = ['Comparison failed', error.message || 'No records were modified.', {error:true}];
    } finally { setBusy(false); }
    if (popup) feedback(...popup);
  });
  download.addEventListener('click', async () => {
    if (!checked || inFlight) return;
    const body = requestBody({download:'csv'});
    setBusy(true, 'Preparing comparison', 'Generating a CSV with new and differing records…');
    try {
      const response = await fetch(form.dataset.compareUrl, {method:'POST', body, credentials:'same-origin'});
      if (!response.ok) throw new Error('Unable to generate the comparison CSV.');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = 'graduate_registry_differences.csv';
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      note('Comparison CSV downloaded. Registry records remain unchanged.', 'success');
    } catch (error) {
      note(error.message, 'error');
      feedback('Download failed', error.message, {error:true});
    } finally { setBusy(false); }
  });
  // Import is a two-action workflow: explicit approval checkbox, followed by a
  // second native confirmation modal. Merely comparing never writes data.
  commit.addEventListener('click', () => {
    if (!checked || !consent.checked || inFlight || imported || !hasImportable()) return;
    const incoming = total('new');
    const updates = total('update');
    const review = total('review') + total('skipped');
    find('grConfirmMessage').textContent =
      `Import ${incoming} new graduate${incoming === 1 ? '' : 's'} and apply ${updates} safe update${updates === 1 ? '' : 's'}?`;
    find('grConfirmCounts').textContent =
      `${total('unchanged')} already match. ${review} need manual review or will be skipped.`;
    if (!confirmDialog.open) showDialog(confirmDialog);
    confirmCancel.focus();
  });

  confirmProceed.addEventListener('click', async () => {
    if (!checked || !consent.checked || inFlight || imported || !hasImportable() || !confirmDialog.open) return;
    // Serialize while the form is still enabled, then block the UI.
    const body = requestBody({confirmed:'yes', review_receipt:comparison?.review_receipt || ''});
    closeDialog(confirmDialog);
    let popup = null;
    setBusy(true, 'Importing graduates', 'Saving eligible new records and safe updates. Do not close this page.');
    try {
      const data = await post(form.dataset.importUrl, body);
      imported = true;
      checked = false;
      consent.checked = false;
      result.hidden = true; // Prevent a now-stale comparison from remaining actionable.
      status.hidden = true;
      popup = ['Import completed', `${data.created} new graduates added, ${data.updated} existing records updated, and ${data.skipped} skipped or flagged for review.`, {refresh:true}];
    } catch (error) {
      note(error.message || 'Import failed; no changes were saved.', 'error');
      popup = ['Import not completed', error.message || 'No changes were saved.', {error:true}];
      // A signed review receipt might be stale; always require another comparison.
      checked = false;
      consent.checked = false;
      commit.disabled = true;
    } finally { setBusy(false); }
    if (popup) feedback(...popup);
  });
})();
