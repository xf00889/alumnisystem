/* Accessible filename feedback for the existing Django multipart file inputs. */
(() => {
  'use strict';
  document.querySelectorAll('.alumni-job-application .job-file-picker input[type="file"]').forEach(input => {
    const name = input.closest('.job-file-picker').querySelector('.job-file-picker__name');
    const update = () => {
      const files = input.files;
      if (!files || files.length === 0) {
        name.textContent = 'No file selected';
        name.classList.remove('has-file');
        return;
      }
      name.textContent = files.length === 1 ? files[0].name : `${files.length} files selected`;
      name.classList.add('has-file');
    };
    input.addEventListener('change', update);
    update();
  });
})();
