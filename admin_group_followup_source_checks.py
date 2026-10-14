"""Offline checks. Live Django tests are still required."""
from pathlib import Path
r=Path(__file__).parent
checks={
 'Admin group availability POST route': "name='set_group_availability'" in (r/'alumni_groups/urls.py').read_text(),
 'Admin-only group status check': 'if not is_administration_account(request.user)' in (r/'alumni_groups/views.py').read_text(),
 'Reason validation': '10 <= len(reason) <= 500' in (r/'alumni_groups/views.py').read_text(),
 'Member notification': 'Notification.objects.bulk_create' in (r/'alumni_groups/views.py').read_text(),
 'Disabled groups hidden': 'else AlumniGroup.objects.filter(is_active=True)' in (r/'alumni_groups/views.py').read_text(),
 'Group membership join protected': "def join_group(request, slug):" in (r/'alumni_groups/views.py').read_text() and 'if is_administration_account(request.user)' in (r/'alumni_groups/views.py').read_text(),
 'New admin modal': 'adminGroupSummaryModal' in (r/'templates/alumni_groups/partials/admin_group_modals.html').read_text(),
 'No admin Join in card': '{% if is_administration_directory %}' in (r/'templates/alumni_groups/group_list.html').read_text(),
 'Admin directory connect hidden': 'if not can_view_alumni_details and user.is_authenticated' in (r/'templates/alumni_directory/alumni_list.html').read_text(),
 'Backend message blocked': "Administration accounts cannot send alumni messages" in (r/'connections/views.py').read_text(),
 'Extended profile moved to Personal': 'Alumni Profile Details' in (r/'templates/alumni_directory/partials/alumni_detail_modal.html').read_text(),
 'Extended profile not under More': 'Extended Alumni Profile' not in (r/'templates/alumni_directory/partials/alumni_detail_modal.html').read_text(),
 'Request dashed border removed': 'border: 0 !important' in (r/'static/css/alumni/connection-requests.css').read_text(),
 'Previous moderation fields preserved': 'resolution_note = models.CharField' in (r/'alumni_groups/models.py').read_text(),
 'Previous secure join preserved': 'Please answer this required membership question.' in (r/'alumni_groups/views.py').read_text(),
}
for name, passed in checks.items(): print(('PASS' if passed else 'FAIL'),name)
assert all(checks.values()), 'Source checks failed'
print(f'{len(checks)}/{len(checks)} source checks passed')
