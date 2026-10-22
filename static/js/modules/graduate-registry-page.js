/** Dedicated registrar comparison workflow. No write request until explicit confirmation. */
(function () {
  'use strict';
  const form = document.getElementById('grImportForm');
  if (!form) return;
  const file = document.getElementById('grImportFile');
  const campus = document.getElementById('grImportCampus');
  const year = document.getElementById('grImportYear');
  const compare = document.getElementById('grCompareButton');
  const download = document.getElementById('grExportComparison');
  const commit = document.getElementById('grCommitButton');
  const consent = document.getElementById('grConfirmCheckbox');
  const status = document.getElementById('grImportStatus');
  const result = document.getElementById('grComparison');
  const summary = document.getElementById('grComparisonMetrics');
  const rows = document.getElementById('grComparisonRows');
  const hint = document.getElementById('grComparisonHint');
  let comparing = false;
  let checked = false;
  let imported = false;

  function invalidate() {
    checked = false;
    imported = false;
    consent.checked = false;
    commit.disabled = true;
    download.disabled = true;
    result.hidden = true;
    status.hidden = true;
  }
  [file, campus, year].forEach((el) => el.addEventListener('change', invalidate));
  consent.addEventListener('change', () => { commit.disabled = !checked || !consent.checked || comparing || imported; });

  function note(message, type='info', busy=false) {
    status.hidden = false;
    status.dataset.type = type;
    status.textContent = message;
    status.setAttribute('aria-busy', busy ? 'true' : 'false');
  }
  function markBusy(busy, action) {
    comparing = busy;
    compare.disabled = busy;
    download.disabled = busy || !checked;
    commit.disabled = busy || !checked || !consent.checked || imported;
    file.disabled = busy; campus.disabled = busy; year.disabled = busy;
    if (busy) note(action, 'info', true);
  }
  function requestBody(extra={}) {
    const body = new FormData(form);
    Object.entries(extra).forEach(([key, value]) => body.set(key, value));
    return body;
  }
  async function post(url, body) {
    const token = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const response = await fetch(url, {
      method:'POST', body, credentials:'same-origin',
      headers: { 'X-CSRFToken': token || '', 'Accept': 'application/json', 'X-Requested-With':'XMLHttpRequest' },
    });
    const json = await response.json().catch(() => null);
    if (!response.ok || !json?.ok) throw new Error(json?.message || 'The request could not be completed.');
    return json;
  }
  const counts = [['new','New'],['unchanged','Matches'],['update','Updates'],['review','Needs review'],['skipped','Skipped']];
  function renderComparison(data) {
    summary.replaceChildren();
    counts.forEach(([key,label]) => {
      const card=document.createElement('div');
      const number=document.createElement('strong'); number.textContent=String(data.totals?.[key] || 0);
      const caption=document.createElement('span'); caption.textContent=label;
      card.append(number,caption); summary.appendChild(card);
    });
    rows.replaceChildren();
    data.rows.forEach((item) => {
      const tr=document.createElement('tr');
      ['source','name','year','campus','course'].forEach((key) => {
        const td=document.createElement('td'); td.textContent=String(item[key] || '—'); tr.appendChild(td);
      });
      const state=document.createElement('td');
      const chip=document.createElement('span');
      chip.className='gr-pill gr-pill--'+(counts.some(([key]) => key===item.status)?item.status:'review');
      chip.textContent=({new:'New',update:'Update',unchanged:'Matches',review:'Review',skipped:'Skipped'})[item.status]||'Review';
      state.appendChild(chip); tr.appendChild(state);
      const reason=document.createElement('td'); reason.textContent=item.changes || '—'; tr.appendChild(reason);
      rows.appendChild(tr);
    });
    hint.textContent=`Showing ${data.shown} of ${data.total_rows} rows. Download the comparison CSV to review every row. Records marked Review or Skipped will not be imported.`;
    result.hidden = false;
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (comparing || !form.reportValidity()) return;
    if (!/\.(csv|xlsx)$/i.test(file.files?.[0]?.name || '')) return note('Choose a CSV or XLSX registrar file.','error');
    if (file.files[0].size > 10 * 1024 * 1024) return note('File exceeds the 10 MB limit.','error');
    checked = false; imported = false; result.hidden = true; consent.checked=false;
    const body = requestBody();
    markBusy(true, 'Comparing the uploaded file with the existing registry…');
    try {
      const data = await post(form.dataset.compareUrl, body);
      renderComparison(data);
      checked = true;
      note('Comparison complete. Review the changes and confirm before importing.', 'success');
    } catch (error) {
      checked = false;
      note(error.message || 'Comparison failed; no changes were made.', 'error');
    } finally { markBusy(false); }
  });
  download.addEventListener('click', async () => {
    if (!checked || comparing) return;
    const body = requestBody({download:'csv'});
    markBusy(true,'Preparing the full comparison CSV…');
    try {
      const response=await fetch(form.dataset.compareUrl,{method:'POST',body,credentials:'same-origin'});
      if(!response.ok) throw Error('Unable to generate the comparison CSV.');
      const blob=await response.blob();
      const url=URL.createObjectURL(blob);
      const a=document.createElement('a'); a.href=url; a.download='graduate_registry_comparison.csv';
      document.body.appendChild(a);a.click();a.remove();
      URL.revokeObjectURL(url);
      note('Comparison file prepared. Your registry is unchanged.','success');
    }catch(error){note(error.message,'error');}finally{markBusy(false);}
  });
  commit.addEventListener('click', async () => {
    if(!checked || !consent.checked || comparing || imported) return;
    const body = requestBody({confirmed:'yes'});
    markBusy(true,'Import in progress… Please keep this page open.');
    try {
      const data=await post(form.dataset.importUrl,body);
      imported=true;
      note(`Import complete: ${data.created} new, ${data.updated} matched/updated, ${data.skipped} needing review or skipped. Refresh the registry to see the updated list.`, 'success');
      commit.textContent='Import completed';
      const link=document.createElement('a');link.href=window.location.pathname;link.className='btn btn-outline-primary ms-2';link.textContent='Refresh registry';
      status.appendChild(document.createTextNode(' '));status.appendChild(link);
    }catch(error){note(error.message,'error');}finally{markBusy(false);}
  });
})();
