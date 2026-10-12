/* Honest, client-side waiting state for the existing synchronous scraper POST.
   Real per-source job counts are unavailable until the server responds. */
(() => {
  'use strict';

  const form = document.getElementById('jobScraperForm');
  if (!form) return;

  const sources = Array.from(form.querySelectorAll('input[name="sources"][type="checkbox"]'));
  const count = document.getElementById('scraperSourcesCount');
  const error = document.getElementById('scraperSourcesError');
  const submit = document.getElementById('runScraperButton');
  const submitLabel = document.getElementById('runScraperButtonLabel');
  const progress = document.getElementById('scraperProgress');
  const progressMessage = document.getElementById('scraperProgressMessage');
  const elapsed = document.getElementById('scraperElapsed');
  const note = document.getElementById('scraperProgressNote');
  const allButton = document.getElementById('scraperSelectAll');
  const clearButton = document.getElementById('scraperClearAll');
  let submitting = false;
  let ticker = null;

  function selected() {
    return sources.filter(source => source.checked);
  }

  function updateSelection() {
    const total = selected().length;
    if (count) count.textContent = `${total} of ${sources.length} selected`;
    if (error && total > 0) error.hidden = true;
  }

  sources.forEach(source => source.addEventListener('change', updateSelection));
  if (allButton) allButton.addEventListener('click', () => {
    sources.forEach(source => { source.checked = true; });
    updateSelection();
  });
  if (clearButton) clearButton.addEventListener('click', () => {
    sources.forEach(source => { source.checked = false; });
    updateSelection();
  });

  function resetWaitingState() {
    if (ticker !== null) clearInterval(ticker);
    ticker = null;
    submitting = false;
    if (progress) progress.hidden = true;
    if (submit) {
      submit.classList.remove('is-busy');
      submit.removeAttribute('aria-disabled');
    }
    if (submitLabel) submitLabel.textContent = 'Run Scraper';
    if (elapsed) elapsed.textContent = '0s elapsed';
  }

  form.addEventListener('submit', event => {
    if (submitting) {
      event.preventDefault();
      return;
    }

    // Validate the checkbox group before submitting. Do not disable form fields
    // or the named submit button: the Django view requires run_scraper in POST.
    const currentSources = selected();
    if (currentSources.length === 0) {
      event.preventDefault();
      if (error) {
        error.hidden = false;
        error.scrollIntoView({block:'nearest'});
      }
      if (sources[0]) sources[0].focus();
      return;
    }

    submitting = true;
    if (submit) {
      submit.classList.add('is-busy');
      submit.setAttribute('aria-disabled', 'true');
    }
    if (submitLabel) submitLabel.textContent = 'Scraping…';
    if (progressMessage) progressMessage.textContent = `Checking ${currentSources.length} selected job site${currentSources.length === 1 ? '' : 's'}. Please keep this tab open.`;
    if (progress) progress.hidden = false;
    if (note) note.textContent = 'This is an activity indicator, not a completion percentage. Saved results will appear when the server responds.';
    const startedAt = Date.now();
    ticker = setInterval(() => {
      const seconds = Math.floor((Date.now() - startedAt) / 1000);
      if (elapsed) elapsed.textContent = `${Math.floor(seconds / 60) > 0 ? `${Math.floor(seconds / 60)}m ` : ''}${seconds % 60}s elapsed`;
      if (seconds >= 60 && note) note.textContent = 'Still working. Some sites may be slower or unavailable; please wait for the server response.';
    }, 1000);
  });

  // A back-forward cache restoration should not leave an old progress indicator
  // or an unusable submit button on the restored form.
  window.addEventListener('pageshow', event => {
    if (event.persisted) resetWaitingState();
  });
  updateSelection();
})();
