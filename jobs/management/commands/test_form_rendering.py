from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from jobs.forms import JobPostingForm, RequiredDocumentFormSet


class Command(BaseCommand):
    help = 'Test job posting form rendering to debug JavaScript issues'

    def handle(self, *args, **options):
        self.stdout.write('=== TESTING JOB POSTING FORM RENDERING ===')
        
        # Create forms
        form = JobPostingForm()
        document_formset = RequiredDocumentFormSet()
        
        # Test management form rendering
        self.stdout.write('\n=== MANAGEMENT FORM HTML ===')
        mgmt_form_html = str(document_formset.management_form)
        self.stdout.write(mgmt_form_html)
        
        # Test if management form contains expected fields
        expected_fields = [
            'required_documents-TOTAL_FORMS',
            'required_documents-INITIAL_FORMS',
            'required_documents-MIN_NUM_FORMS',
            'required_documents-MAX_NUM_FORMS'
        ]
        
        self.stdout.write('\n=== MANAGEMENT FORM FIELD CHECK ===')
        for field_name in expected_fields:
            if field_name in mgmt_form_html:
                self.stdout.write(f'✓ {field_name} found')
            else:
                self.stdout.write(f'✗ {field_name} MISSING')
        
        # Test first form rendering
        if document_formset.forms:
            self.stdout.write('\n=== FIRST FORM FIELDS ===')
            form = document_formset.forms[0]
            for field_name, field in form.fields.items():
                bound_field = form[field_name]
                self.stdout.write(f'{field_name}: name="{bound_field.html_name}" id="{bound_field.id_for_label}"')
        
        # Test template rendering (simplified)
        self.stdout.write('\n=== TEMPLATE CONTEXT TEST ===')
        context = {
            'form': form,
            'document_formset': document_formset
        }
        
        # Test if we can access the formset in template context
        self.stdout.write(f'Form valid: {form.is_valid()}')
        self.stdout.write(f'Formset prefix: {document_formset.prefix}')
        self.stdout.write(f'Formset form count: {len(document_formset.forms)}')
        
        self.stdout.write('\n=== TEST COMPLETE ===')
