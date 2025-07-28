console.log('Job posting JavaScript file loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing job posting JavaScript');

    // Initialize document formset functionality
    initializeDocumentFormset();
});

function initializeDocumentFormset() {
    console.log('=== INITIALIZING DOCUMENT FORMSET ===');
    
    // Find required elements
    const documentFormsContainer = document.getElementById('document-forms');
    const addDocumentBtn = document.getElementById('add-document');
    let managementForm = document.querySelector('[name="required_documents-TOTAL_FORMS"]');
    
    // Alternative selector for management form
    if (!managementForm) {
        managementForm = document.querySelector('[name$="-TOTAL_FORMS"]');
    }
    
    console.log('Element detection:');
    console.log('- documentFormsContainer:', documentFormsContainer);
    console.log('- addDocumentBtn:', addDocumentBtn);
    console.log('- managementForm:', managementForm);
    
    // Check if all required elements are present
    if (!documentFormsContainer || !addDocumentBtn || !managementForm) {
        console.warn('Required elements not found. Missing:');
        if (!documentFormsContainer) console.warn('- document-forms container');
        if (!addDocumentBtn) console.warn('- add-document button');
        if (!managementForm) console.warn('- management form');

        // Try alternative selectors for debugging
        console.log('Trying alternative selectors...');
        const altContainer = document.querySelector('[id*="document"]');
        const altButton = document.querySelector('button[class*="add-document"]');
        const altMgmt = document.querySelector('input[name*="TOTAL_FORMS"]');

        console.log('Alternative container:', altContainer);
        console.log('Alternative button:', altButton);
        console.log('Alternative management form:', altMgmt);

        return;
    }
    
    console.log('✓ All required elements found');
    
    // Initialize form count
    let formCount = parseInt(managementForm.value) || 0;
    console.log('Initial form count:', formCount);
    
    // Function to create new document form
    function addDocumentForm() {
        console.log('=== ADDING NEW DOCUMENT FORM ===');
        console.log('Current form count:', formCount);
        
        // Get template HTML
        const templateHtml = getEmptyFormTemplate();
        
        // Replace __prefix__ with actual form number
        const newFormHtml = templateHtml.replace(/__prefix__/g, formCount);
        
        // Create new form container
        const newFormDiv = document.createElement('div');
        newFormDiv.className = 'document-requirement';
        newFormDiv.innerHTML = newFormHtml;
        
        // Add delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn btn-danger btn-sm mt-2';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Remove';
        deleteBtn.addEventListener('click', function() {
            removeDocumentForm(newFormDiv);
        });
        
        newFormDiv.appendChild(deleteBtn);
        
        // Append to container
        documentFormsContainer.appendChild(newFormDiv);
        
        // Update form count
        formCount++;
        managementForm.value = formCount;
        
        console.log('✓ New form added. Form count now:', formCount);
        
        // Update form indices to ensure proper numbering
        updateFormIndices();
    }
    
    // Function to remove document form
    function removeDocumentForm(formElement) {
        console.log('=== REMOVING DOCUMENT FORM ===');
        formElement.remove();
        formCount--;
        managementForm.value = formCount;
        console.log('✓ Form removed. Form count now:', formCount);
        updateFormIndices();
    }
    
    // Function to update form indices
    function updateFormIndices() {
        console.log('=== UPDATING FORM INDICES ===');
        const forms = documentFormsContainer.querySelectorAll('.document-requirement');
        
        forms.forEach((form, index) => {
            // Update all input, select, and textarea elements
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.name) {
                    input.name = input.name.replace(/required_documents-\d+/, `required_documents-${index}`);
                }
                if (input.id) {
                    input.id = input.id.replace(/id_required_documents-\d+/, `id_required_documents-${index}`);
                }
            });
            
            // Update labels
            const labels = form.querySelectorAll('label');
            labels.forEach(label => {
                if (label.getAttribute('for')) {
                    const forAttr = label.getAttribute('for');
                    label.setAttribute('for', forAttr.replace(/id_required_documents-\d+/, `id_required_documents-${index}`));
                }
            });
        });
        
        console.log('✓ Updated indices for', forms.length, 'forms');
    }
    
    // Function to get empty form template
    function getEmptyFormTemplate() {
        // Try to clone existing form first (more reliable with crispy forms)
        const existingForms = documentFormsContainer.querySelectorAll('.document-requirement');
        if (existingForms.length > 0) {
            console.log('Cloning existing form structure');
            const templateForm = existingForms[0].cloneNode(true);
            
            // Clear all input values
            const inputs = templateForm.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.type === 'checkbox') {
                    input.checked = true; // Default to required
                } else if (input.type === 'hidden') {
                    input.value = '';
                } else if (input.name && input.name.includes('file_types')) {
                    input.value = '.pdf,.doc,.docx';
                } else if (input.name && input.name.includes('max_file_size')) {
                    input.value = '5';
                } else {
                    input.value = '';
                }
            });
            
            // Remove any existing delete buttons
            const deleteButtons = templateForm.querySelectorAll('.btn-danger');
            deleteButtons.forEach(btn => btn.remove());
            
            return templateForm.innerHTML;
        }
        
        // Fallback template if no existing forms
        console.log('Using fallback template');
        return createFallbackTemplate();
    }
    
    // Fallback template function
    function createFallbackTemplate() {
        return `
            <input type="hidden" name="required_documents-__prefix__-id" id="id_required_documents-__prefix__-id">
            <div class="row">
                <div class="col-md-6 mb-2">
                    <div class="form-group">
                        <label for="id_required_documents-__prefix__-name" class="form-label">Document Name</label>
                        <input type="text" name="required_documents-__prefix__-name" class="form-control" id="id_required_documents-__prefix__-name" required>
                    </div>
                </div>
                <div class="col-md-6 mb-2">
                    <div class="form-group">
                        <label for="id_required_documents-__prefix__-document_type" class="form-label">Document Type</label>
                        <select name="required_documents-__prefix__-document_type" class="form-control" id="id_required_documents-__prefix__-document_type" required>
                            <option value="">---------</option>
                            <option value="RESUME">Resume/CV</option>
                            <option value="COVER_LETTER">Cover Letter</option>
                            <option value="TRANSCRIPT">Transcript of Records</option>
                            <option value="DIPLOMA">Diploma</option>
                            <option value="CERTIFICATION">Certification</option>
                            <option value="PORTFOLIO">Portfolio</option>
                            <option value="RECOMMENDATION">Recommendation Letter</option>
                            <option value="GOVERNMENT_ID">Government ID</option>
                            <option value="OTHER">Other Document</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12 mb-2">
                    <div class="form-group">
                        <label for="id_required_documents-__prefix__-description" class="form-label">Description</label>
                        <textarea name="required_documents-__prefix__-description" class="form-control" id="id_required_documents-__prefix__-description" rows="3"></textarea>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-4 mb-2">
                    <div class="form-group">
                        <label for="id_required_documents-__prefix__-file_types" class="form-label">Allowed File Types</label>
                        <input type="text" name="required_documents-__prefix__-file_types" class="form-control" id="id_required_documents-__prefix__-file_types" value=".pdf,.doc,.docx">
                    </div>
                </div>
                <div class="col-md-4 mb-2">
                    <div class="form-group">
                        <label for="id_required_documents-__prefix__-max_file_size" class="form-label">Max File Size (MB)</label>
                        <input type="number" name="required_documents-__prefix__-max_file_size" class="form-control" id="id_required_documents-__prefix__-max_file_size" value="5" min="1" max="50">
                    </div>
                </div>
                <div class="col-md-4 mb-2">
                    <div class="form-group">
                        <div class="form-check">
                            <input type="checkbox" name="required_documents-__prefix__-is_required" class="form-check-input" id="id_required_documents-__prefix__-is_required" checked>
                            <label class="form-check-label" for="id_required_documents-__prefix__-is_required">
                                This document is required
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add event listener to the add button
    addDocumentBtn.addEventListener('click', function(e) {
        console.log('=== ADD DOCUMENT BUTTON CLICKED ===');
        e.preventDefault();
        addDocumentForm();
    });
    
    // Add delete functionality to existing forms
    const existingForms = documentFormsContainer.querySelectorAll('.document-requirement');
    existingForms.forEach(form => {
        if (!form.querySelector('.btn-danger')) {
            const deleteBtn = document.createElement('button');
            deleteBtn.type = 'button';
            deleteBtn.className = 'btn btn-danger btn-sm mt-2';
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Remove';
            deleteBtn.addEventListener('click', function() {
                removeDocumentForm(form);
            });
            form.appendChild(deleteBtn);
        }
    });
    
    // Add global test function for debugging
    window.testAddDocument = function() {
        console.log('=== MANUAL TEST FUNCTION ===');
        addDocumentForm();
    };
    
    console.log('✓ Document formset initialization complete');
}

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const jobForm = document.getElementById('jobForm');
    if (jobForm) {
        jobForm.addEventListener('submit', function(e) {
            console.log('Form submission validation');
            const requiredFields = jobForm.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    }
});
