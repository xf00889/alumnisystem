/* Single alumni editing destination: independently persisted profile sections.
   Existing staff/admin form submission continues to use the legacy handler. */
(() => {
  'use strict';
  const names = ['personal', 'education', 'experience', 'skills', 'documents'];
  const idFor = {personal:'collapsePersonal', education:'collapseEducation',
    experience:'collapseExperience', skills:'collapseSkills', documents:'collapseDocuments'};

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('profileForm');
    const nav = document.querySelector('.alumni-profile-edit-tabs');
    if (!form || !nav) return;
    const status = document.getElementById('sectionSaveStatus');
    const buttons = [...nav.querySelectorAll('[data-profile-tab]')];
    const save = document.getElementById('saveSectionButton');
    const saveNext = document.getElementById('saveNextButton');
    const finish = document.getElementById('finishEditingButton');
    const actions = document.getElementById('profileEditorActions');
    const currentFromUrl = new URLSearchParams(location.search);
    let current = names.includes(currentFromUrl.get('section')) ? currentFromUrl.get('section') : 'personal';
    let dirty = false;
    let saving = false;

    const panelFor = (section) => document.getElementById(idFor[section]);
    const labelFor = (name) => name === 'personal' ? 'Personal information' : name[0].toUpperCase() + name.slice(1);
    const setStatus = (message, kind = '') => {
      status.textContent = message;
      status.dataset.state = kind;
    };
    const select = (name, focusTab = false) => {
      if (!names.includes(name)) return;
      current = name;
      names.forEach((section) => {
        const panel = panelFor(section);
        const selected = section === name;
        panel.classList.toggle('show', selected);
        panel.setAttribute('role','tabpanel');
        panel.setAttribute('aria-hidden', String(!selected));
        const item = panel.closest('.accordion-item');
        item.hidden = !selected;
        const btn = buttons.find((b) => b.dataset.profileTab === section);
        btn.classList.toggle('active', selected);
        btn.setAttribute('aria-selected', String(selected));
        btn.tabIndex = selected ? 0 : -1;
        panel.setAttribute('aria-labelledby', btn.id || ('profile-tab-' + section));
        btn.id = 'profile-tab-' + section;
      });
      // Keep save controls at the end of the visible tab instead of in a floating bar.
      const activeBody = panelFor(name).querySelector('.accordion-body');
      if (actions && activeBody) activeBody.appendChild(actions);
      if (focusTab) buttons.find((b) => b.dataset.profileTab === name).focus();
      saveNext.disabled = name === 'documents';
      saveNext.textContent = name === 'documents' ? 'Last section' : 'Save & Next →';
    };
    select(current);
    if (currentFromUrl.get('saved') === '1') {
      setStatus('Your section was saved. Continue whenever you are ready.', 'success');
    }

    buttons.forEach((button) => {
      button.addEventListener('click', () => {
        // Switching tabs preserves in-page inputs, but they are NOT saved automatically.
        if (dirty) {
          if (!window.confirm('This section has unsaved changes. Discard them and switch tabs?')) return;
          dirty = false;
          location.assign(form.dataset.editUrl + '?section=' + encodeURIComponent(button.dataset.profileTab));
          return;
        }
        select(button.dataset.profileTab);
        setStatus(dirty ? 'You have unsaved edits. Save each changed section before leaving this page.'
          : 'Select Save when you are ready; other sections can wait.', dirty ? 'warning' : '');
      });
      button.addEventListener('keydown', (event) => {
        if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
        event.preventDefault();
        const pos = names.indexOf(button.dataset.profileTab);
        const target = names[(pos + (event.key === 'ArrowRight' ? 1 : names.length - 1)) % names.length];
        if (dirty) {
          if (!window.confirm('Discard unsaved changes and switch tabs?')) return;
          dirty = false;
          location.assign(form.dataset.editUrl + '?section=' + encodeURIComponent(target));
        } else select(target, true);
      });
    });
    form.addEventListener('input', () => { dirty = true; setStatus('Unsaved changes — select Save to keep them.', 'warning'); });
    form.addEventListener('change', () => { dirty = true; setStatus('Unsaved changes — select Save to keep them.', 'warning'); });
    window.addEventListener('beforeunload', (event) => {
      if (dirty && !saving) { event.preventDefault(); event.returnValue = ''; }
    });
    finish?.addEventListener('click', (event) => {
      if (dirty && !window.confirm('Some changes have not been saved. Return to your profile anyway?')) event.preventDefault();
      else dirty = false;
    });

    const errorBox = document.createElement('div');
    errorBox.id = 'sectionValidationErrors';
    errorBox.className = 'alumni-profile-errors';
    errorBox.setAttribute('role','alert');
    errorBox.hidden = true;
    nav.insertAdjacentElement('afterend', errorBox);

    const persist = async (advance = false) => {
      if (saving) return;
      saving = true;
      save.disabled = true;
      saveNext.disabled = true;
      errorBox.hidden = true;
      setStatus('Saving ' + labelFor(current).toLowerCase() + '…', 'saving');
      const data = new FormData();
      data.set('section', current);
      data.set('csrfmiddlewaretoken', form.querySelector('[name="csrfmiddlewaretoken"]').value);
      const panel = panelFor(current);
      panel.querySelectorAll('input[name],select[name],textarea[name]').forEach((input) => {
        if (input.disabled || ['button','submit','reset'].includes(input.type)) return;
        if ((input.type === 'checkbox' || input.type === 'radio') && !input.checked) return;
        if (input.type === 'file') { if (input.files.length) data.append(input.name, input.files[0]); }
        else data.append(input.name, input.value);
      });
      try {
        const response = await fetch(form.dataset.sectionSaveUrl, {
          method: 'POST', body: data,
          headers: {'X-CSRFToken': data.get('csrfmiddlewaretoken'), 'X-Requested-With': 'XMLHttpRequest'},
          credentials: 'same-origin'
        });
        const result = await response.json();
        if (!response.ok || result.status !== 'success') {
          const problems = Array.isArray(result.errors) ? result.errors : [];
          const list = document.createElement('ul');
          (problems.length ? problems : [{label:'Save',messages:[result.message || 'Please check your entries.']}]).forEach((problem) => {
            (problem.messages || []).forEach((message) => {
              const li = document.createElement('li');
              li.textContent = (problem.label ? problem.label + ': ' : '') + message;
              list.appendChild(li);
            });
          });
          errorBox.replaceChildren(list);
          errorBox.hidden = false;
          errorBox.scrollIntoView({behavior:'smooth',block:'center'});
          setStatus('Not saved. Please correct the errors in this section.', 'error');
          return;
        }
        dirty = false;
        // Reload to get fresh server-assigned IDs after saving new formset entries.
        // Prevents a repeated save from inserting duplicate records.
        saving = true;
        const next = advance ? names[Math.min(names.indexOf(current) + 1, names.length - 1)] : current;
        location.assign(form.dataset.editUrl + '?section=' + encodeURIComponent(next) + '&saved=1');
      } catch (error) {
        setStatus('Unable to save. Check your connection and try again; your inputs are still on this page.', 'error');
      } finally {
        saving = false;
        save.disabled = false;
        saveNext.disabled = current === 'documents';
      }
    };

    // Capture the form submit before the legacy all-section AJAX handler.
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      persist(false);
    }, true);
    saveNext.addEventListener('click', () => persist(true));
  });
})();
