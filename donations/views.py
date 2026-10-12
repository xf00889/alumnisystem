from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, FileResponse, HttpResponseRedirect, Http404
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse

from .models import Campaign, CampaignType, Donation, DonorRecognition, CampaignUpdate, GCashConfig
from .forms import DonationForm, CampaignFilterForm, CampaignForm, PaymentProofForm, DonationVerificationForm
from accounts.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db import models
from .forms_gcash import GCashConfigForm
import logging
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.cache import never_cache
from .payment_flow import (assert_campaign_accepts_donations, resolve_recipient, snapshot_recipient,
                           grant_guest_access, assert_donation_access, email_guest_recovery_link, payment_display)

logger = logging.getLogger(__name__)

# Preserve donor URL privacy without breaking browser form POSTs. A document
# with Referrer-Policy: no-referrer sends Origin: null on navigation-mode POST,
# which Django correctly rejects even when the CSRF token is valid.
# strict-origin sends the site's origin (not donation paths or guest claims)
# for same-origin proof submissions. Never whitelist the "null" origin.
DONATION_REFERRER_POLICY = 'strict-origin'


def can_manage_donations(user):
    """Check if user can manage donations (staff, superuser, or alumni coordinator)"""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    try:
        return user.profile.is_alumni_coordinator
    except:
        return False


def public_campaign_list(request):
    """Guest campaign directory using the university's public website design.

    Reuse the same read-only campaign filtering and pagination. Never expose
    alumni-only, draft, paused, or unavailable campaigns to visitors.
    """
    if request.user.is_authenticated:
        return redirect('donations:campaign_list')

    now = timezone.now()
    campaigns = Campaign.objects.filter(
        visibility='public', status='active', allow_donations=True,
        start_date__lte=now,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=now))
    context = _campaign_list_context(request, campaigns)
    return render(request, 'donations/public_campaign_list.html', context)


def campaign_list(request):
    """Campaign directory for authenticated alumni and management accounts."""
    if not request.user.is_authenticated:
        url = reverse('donations:public_campaign_list')
        params = request.GET.urlencode()
        return redirect(f'{url}?{params}' if params else url)
    campaigns = Campaign.objects.filter(
        Q(visibility='registered_alumni') | Q(visibility='public')
    ).exclude(Q(status__in=['completed', 'cancelled']) | Q(end_date__lt=timezone.now()))
    context = _campaign_list_context(request, campaigns)
    return render(request, 'donations/campaign_list.html', context)


def _campaign_list_context(request, campaigns):
    """Common filtering and pagination for public and alumni campaigns."""
    # Apply filters from form
    filter_form = CampaignFilterForm(request.GET)
    if filter_form.is_valid():
        # Filter by search term
        search = filter_form.cleaned_data.get('search')
        if search:
            campaigns = campaigns.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )

        # Filter by campaign type
        campaign_type = filter_form.cleaned_data.get('campaign_type')
        if campaign_type:
            campaigns = campaigns.filter(campaign_type__slug=campaign_type)

        # Filter by status
        status = filter_form.cleaned_data.get('status')
        if status:
            campaigns = campaigns.filter(status=status)

        # Filter by visibility
        visibility = filter_form.cleaned_data.get('visibility')
        if visibility:
            campaigns = campaigns.filter(visibility=visibility)

        # Apply sorting
        sort = filter_form.cleaned_data.get('sort', 'recent')
        if sort == 'recent':
            campaigns = campaigns.order_by('-start_date')
        elif sort == 'ending_soon':
            # Get active campaigns with end dates and order by closest end date
            now = timezone.now()
            campaigns = campaigns.filter(
                status='active',
                end_date__isnull=False,
                end_date__gt=now
            ).order_by('end_date')
        elif sort == 'progress':
            # This is a bit tricky since progress is calculated
            # We'll need to annotate with the sum of donations
            campaigns = campaigns.annotate(
                total_donations=Sum('donations__amount', filter=Q(donations__status='completed'))
            ).order_by('-total_donations')
        elif sort == 'goal':
            campaigns = campaigns.order_by('-goal_amount')

    # Get campaign types for sidebar
    campaign_types = CampaignType.objects.annotate(
        campaign_count=Count('campaigns')
    ).order_by('name')

    # Paginate results
    paginator = Paginator(campaigns, 9)  # 9 campaigns per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'campaign_types': campaign_types,
    }

    return context

def campaign_detail(request, slug):
    """View to display campaign details and donation form"""
    campaign = get_object_or_404(Campaign, slug=slug)
    
    # Check visibility permissions
    if not request.user.is_authenticated and campaign.visibility == 'registered_alumni':
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    # Get recent donations for this campaign (including both anonymous and non-anonymous)
    recent_donations = Donation.objects.filter(
        campaign=campaign,
        status='completed'
    ).select_related('donor').order_by('-donation_date')[:10]

    # Get campaign updates
    updates = campaign.updates.all().order_by('-created')

    # Get donation statistics
    donation_stats = {
        'total_donors': Donation.objects.filter(
            campaign=campaign,
            status='completed'
        ).values('donor').distinct().count(),
        'total_amount': campaign.current_amount,
        'progress_percentage': campaign.progress_percentage,
    }

    # Reject invalid campaign states on POST, regardless of client-side controls.
    campaign_open = (campaign.status == 'active' and campaign.allow_donations and
                     campaign.start_date <= timezone.now() and
                     (not campaign.end_date or campaign.end_date >= timezone.now()))
    form = DonationForm(request.POST or None, user=request.user, campaign=campaign)
    if request.method == 'POST':
        try:
            assert_campaign_accepts_donations(campaign, request.user)
            config = resolve_recipient(campaign)
        except ValidationError as exc:
            form.add_error(None, exc.messages[0])
        else:
            if form.is_valid():
                with transaction.atomic():
                    donation = form.save()
                    snapshot_recipient(donation, config)
                    if not request.user.is_authenticated:
                        grant_guest_access(request, donation)
                    email_guest_recovery_link(donation, request)
                messages.info(request, _('Donation amount saved. No payment has been taken. Follow the GCash instructions to transfer the exact amount.'))
                return redirect('donations:payment_instructions', pk=donation.pk)

    context = {
        'campaign': campaign,
        'form': form,
        'recent_donations': recent_donations,
        'updates': updates,
        'donation_stats': donation_stats,
        'campaign_open': campaign_open,
    }

    # Use minimal template for unauthenticated users (no navbar)
    if not request.user.is_authenticated:
        return render(request, 'donations/donation_form_minimal.html', context)
    else:
        return render(request, 'donations/campaign_detail.html', context)

@login_required
def donation_history(request):
    """View to display user's donation history"""
    # Donors must be able to resume unpaid intents and track submitted proof.
    donations = (Donation.objects.filter(donor=request.user)
                 .exclude(status='cancelled')
                 .select_related('campaign').order_by('-donation_date'))

    # Calculate statistics (only completed donations)
    completed = donations.filter(status='completed')
    total_donated = completed.aggregate(total=Sum('amount'))['total'] or 0
    campaigns_supported = completed.values('campaign').distinct().count()

    context = {
        'donations': donations,
        'total_donated': total_donated,
        'campaigns_supported': campaigns_supported,
        'donation_count': donations.count(),
    }

    return render(request, 'donations/donation_history.html', context)

@login_required
@require_POST
def cancel_donation(request, pk):
    """Cancel only this donor's unpaid intent; retain record for audit/reconciliation.

    Submitted proof must be reviewed instead of silently discarded. The row lock
    prevents cancellation racing with proof submission or staff verification.
    """
    with transaction.atomic():
        donation = get_object_or_404(
            Donation.objects.select_for_update(), pk=pk, donor=request.user,
        )
        if donation.status != 'pending_payment' or donation.payment_proof or donation.reference_number:
            messages.error(request, _('This donation cannot be cancelled after payment proof is submitted. Contact the alumni office if you already transferred funds.'))
            return redirect('donations:donation_history')
        donation.status = 'cancelled'
        donation.save(update_fields=['status', 'updated_at'])
    logger.info('Donor %s cancelled unpaid donation %s', request.user.pk, pk)
    messages.success(request, _('Unpaid donation cancelled. It has been removed from your active donation history.'))
    return redirect('donations:donation_history')


def donation_confirmation(request, pk):
    """View to display donation confirmation"""
    donation = get_object_or_404(Donation, pk=pk)

    assert_donation_access(request, donation)

    context = {
        'donation': donation,
    }

    if not request.user.is_authenticated:
        template = 'donations/donor_status_guest.html'
    elif can_manage_donations(request.user):
        template = 'donations/donation_confirmation.html'
    else:
        template = 'donations/donor_status.html'
    response = render(request, template, context)
    response['Cache-Control'] = 'private, no-store'
    response['Referrer-Policy'] = DONATION_REFERRER_POLICY
    return response

@login_required
def campaign_donors(request, slug):
    """View to display all donors for a campaign"""
    campaign = get_object_or_404(Campaign, slug=slug)

    # Get only non-anonymous donations to display in the list
    donations = Donation.objects.filter(
        campaign=campaign,
        status='completed',
        is_anonymous=False
    ).select_related('donor').order_by('-amount')

    # Count anonymous donations
    anonymous_count = Donation.objects.filter(
        campaign=campaign,
        status='completed',
        is_anonymous=True
    ).count()

    context = {
        'campaign': campaign,
        'donations': donations,
        'anonymous_count': anonymous_count,
    }

    return render(request, 'donations/campaign_donors.html', context)


@require_POST
@login_required
def update_donation_status(request, pk):
    """Audited status transitions for the administrative donation list."""
    if not can_manage_donations(request.user):
        return JsonResponse({'status': 'error', 'message': _('Permission denied')}, status=403)
    status = request.POST.get('status')
    transitions = {
        'pending_payment': ('failed',),
        'pending_verification': ('completed', 'failed', 'disputed'),
        'completed': ('refunded', 'disputed'),
        'disputed': ('completed', 'failed'),
    }
    with transaction.atomic():
        donation = get_object_or_404(Donation.objects.select_for_update(), pk=pk)
        if status not in transitions.get(donation.status, ()):
            return JsonResponse({'status': 'error', 'message': 'Invalid donation status transition.'}, status=400)
        if status == 'completed' and request.POST.get('gcash_reconciled') != 'yes':
            return JsonResponse({'status': 'error', 'message': 'Confirm actual GCash receipt before approval.'}, status=400)
        if status == 'completed' and (not donation.payment_proof or not donation.reference_number):
            return JsonResponse({'status': 'error', 'message': 'GCash proof and reference number are required before approving.'}, status=400)
        donation.status = status
        donation.verified_by = request.user
        donation.verification_date = timezone.now()
        donation.save()
    logger.info('Donation %s status updated to %s by staff %s', pk, status, request.user.pk)
    return JsonResponse({'status': 'success', 'message': _('Donation status updated successfully'), 'new_status': donation.get_status_display()})

@login_required
def manage_donations(request):
    """View to manage all donations with advanced filtering and bulk actions"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    # Get filter parameters from request
    campaign_id = request.GET.get('campaign')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search')

    # Base queryset
    donations = Donation.objects.all().select_related('campaign', 'donor').order_by('-donation_date')

    # Apply filters
    if campaign_id:
        donations = donations.filter(campaign_id=campaign_id)

    if status:
        donations = donations.filter(status=status)


    if start_date:
        donations = donations.filter(donation_date__gte=start_date)

    if end_date:
        donations = donations.filter(donation_date__lte=end_date)

    if search_query:
        donations = donations.filter(
            Q(donor__first_name__icontains=search_query) |
            Q(donor__last_name__icontains=search_query) |
            Q(donor__email__icontains=search_query) |
            Q(donor_name__icontains=search_query) |
            Q(donor_email__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(campaign__name__icontains=search_query)
        )

    # Get statistics for the filtered donations
    filtered_total = donations.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0

    completed_count = donations.filter(status='completed').count()
    pending_count = donations.filter(status='pending').count()
    failed_count = donations.filter(Q(status='failed') | Q(status='refunded')).count()

    # Pagination
    paginator = Paginator(donations, 20)  # Show 20 donations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Prepare query parameter string for pagination links
    query_params = []
    for key, value in request.GET.items():
        if key != 'page' and value:
            query_params.append(f"{key}={value}")
    query_params = '&'.join(query_params)

    # Get all campaigns for filter dropdown
    all_campaigns = Campaign.objects.all().order_by('name')

    # Get choices for dropdowns
    status_choices = Donation._meta.get_field('status').choices

    context = {
        'donations': page_obj,
        'query_params': query_params,
        'filtered_total': filtered_total,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'all_campaigns': all_campaigns,
        'status_choices': status_choices,
        'selected_campaign': int(campaign_id) if campaign_id and campaign_id.isdigit() else None,
        'selected_status': status,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
    }

    return render(request, 'donations/manage_donations.html', context)

@login_required
def manage_campaigns(request):
    """View to manage all campaigns with filtering and bulk actions"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    # Get filter parameters from request
    status = request.GET.get('status')
    campaign_type_id = request.GET.get('campaign_type')
    search_query = request.GET.get('search')

    # Base queryset
    campaigns = Campaign.objects.all().select_related('campaign_type', 'created_by').order_by('-created_at')

    # Apply filters
    if status:
        campaigns = campaigns.filter(status=status)

    if campaign_type_id:
        campaigns = campaigns.filter(campaign_type_id=campaign_type_id)

    if search_query:
        campaigns = campaigns.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(beneficiaries__icontains=search_query)
        )

    # Update current amounts for campaigns (donors_count and progress_percentage are calculated properties)
    for campaign in campaigns:
        # Update current amount from completed donations
        current_total = Donation.objects.filter(
            campaign=campaign,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Only update if the amount has changed to avoid unnecessary database writes
        if campaign.current_amount != current_total:
            campaign.current_amount = current_total
            campaign.save(update_fields=['current_amount'])

    # Get statistics
    total_campaigns = campaigns.count()
    active_count = sum(1 for c in campaigns if c.status == 'active')
    completed_count = sum(1 for c in campaigns if c.status == 'completed')
    draft_count = sum(1 for c in campaigns if c.status in ['draft', 'paused'])

    # Pagination
    paginator = Paginator(campaigns, 12)  # Show 12 campaigns per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Prepare query parameter string for pagination links
    query_params = []
    for key, value in request.GET.items():
        if key != 'page' and value:
            query_params.append(f"{key}={value}")
    query_params = '&'.join(query_params)

    # Get all campaign types for filter dropdown
    all_campaign_types = CampaignType.objects.all().order_by('name')

    # Get choices for status dropdown
    status_choices = Campaign._meta.get_field('status').choices

    context = {
        'campaigns': page_obj,
        'query_params': query_params,
        'total_campaigns': total_campaigns,
        'active_count': active_count,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'all_campaign_types': all_campaign_types,
        'status_choices': status_choices,
        'selected_status': status,
        'selected_campaign_type': int(campaign_type_id) if campaign_type_id and campaign_type_id.isdigit() else None,
        'search_query': search_query,
    }

    return render(request, 'donations/manage_campaigns.html', context)

@require_POST
@login_required
def delete_donation(request, pk):
    """Delete a donation"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({
            'status': 'error',
            'message': _('You do not have permission to delete donations.')
        })

    donation = get_object_or_404(Donation, pk=pk)

    try:
        donation.delete()
        return JsonResponse({
            'status': 'success',
            'message': _('Donation deleted successfully.')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def donation_edit_form(request, pk):
    """Return HTML form for editing a donation"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({
            'status': 'error',
            'message': _('You do not have permission to edit donations.')
        })

    donation = get_object_or_404(Donation, pk=pk)

    # Generate campaign options
    campaign_options = ""
    for campaign in Campaign.objects.all():
        selected = "selected" if campaign.pk == donation.campaign.pk else ""
        campaign_options += f'<option value="{campaign.pk}" {selected}>{campaign.name}</option>'

    # Generate status options
    status_options = ""
    for status_code, status_name in Donation.STATUS_CHOICES:
        selected = "selected" if status_code == donation.status else ""
        status_options += f'<option value="{status_code}" {selected}>{status_name}</option>'


    # Format donation date for datetime-local input
    donation_date = donation.donation_date.strftime('%Y-%m-%dT%H:%M')

    # Checkboxes
    is_anonymous_checked = "checked" if donation.is_anonymous else ""
    receipt_sent_checked = "checked" if donation.receipt_sent else ""

    # Render the form HTML
    html = f"""
    <form action="{reverse('donations:edit_donation', args=[donation.pk])}" method="post">
        <div class="alert alert-danger d-none" role="alert"></div>

        <div class="row mb-3">
            <div class="col-md-6">
                <label for="id_campaign" class="form-label">Campaign</label>
                <select name="campaign" id="id_campaign" class="form-select" required>
                    {campaign_options}
                </select>
            </div>
            <div class="col-md-6">
                <label for="id_amount" class="form-label">Amount</label>
                <input type="number" name="amount" id="id_amount" class="form-control"
                       value="{donation.amount}" required step="0.01" min="0">
            </div>
        </div>

        <div class="row mb-3">
            <div class="col-md-6">
                <label for="id_status" class="form-label">Status</label>
                <select name="status" id="id_status" class="form-select" required>
                    {status_options}
                </select>
            </div>
        </div>

        <div class="row mb-3">
            <div class="col-md-6">
                <label for="id_donation_date" class="form-label">Donation Date</label>
                <input type="datetime-local" name="donation_date" id="id_donation_date" class="form-control"
                       value="{donation_date}" required>
            </div>
            <div class="col-md-6">
                <label for="id_reference_number" class="form-label">Reference Number</label>
                <input type="text" name="reference_number" id="id_reference_number" class="form-control"
                       value="{donation.reference_number}">
            </div>
        </div>

        <div class="row mb-3">
            <div class="col-md-6">
                <div class="form-check">
                    <input type="checkbox" name="is_anonymous" id="id_is_anonymous" class="form-check-input"
                           {is_anonymous_checked}>
                    <label for="id_is_anonymous" class="form-check-label">Anonymous Donation</label>
                </div>
            </div>
            <div class="col-md-6">
                <div class="form-check">
                    <input type="checkbox" name="receipt_sent" id="id_receipt_sent" class="form-check-input"
                           {receipt_sent_checked}>
                    <label for="id_receipt_sent" class="form-check-label">Receipt Sent</label>
                </div>
            </div>
        </div>

        <div class="mb-3">
            <label for="id_message" class="form-label">Message</label>
            <textarea name="message" id="id_message" class="form-control" rows="3">{donation.message}</textarea>
        </div>

        <div class="row mb-3">
            <div class="col-md-6">
                <label for="id_donor_name" class="form-label">Donor Name (if not registered)</label>
                <input type="text" name="donor_name" id="id_donor_name" class="form-control"
                       value="{donation.donor_name}">
            </div>
            <div class="col-md-6">
                <label for="id_donor_email" class="form-label">Donor Email (if not registered)</label>
                <input type="email" name="donor_email" id="id_donor_email" class="form-control"
                       value="{donation.donor_email}">
            </div>
        </div>

        <div class="text-end">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="submit" class="btn btn-primary">Save Changes</button>
        </div>
    </form>
    """

    return HttpResponse(html)

@require_POST
@login_required
def edit_donation(request, pk):
    """Edit a donation"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({
            'status': 'error',
            'message': _('You do not have permission to edit donations.')
        })

    donation = get_object_or_404(Donation, pk=pk)

    try:
        # Update fields from form data
        campaign_id = request.POST.get('campaign')
        if campaign_id:
            donation.campaign = get_object_or_404(Campaign, pk=campaign_id)

        amount = request.POST.get('amount')
        if amount:
            donation.amount = amount

        status = request.POST.get('status')
        if status:
            donation.status = status


        donation_date = request.POST.get('donation_date')
        if donation_date:
            donation.donation_date = donation_date

        donation.reference_number = request.POST.get('reference_number', '')
        donation.is_anonymous = request.POST.get('is_anonymous') == 'on'
        donation.donor_name = request.POST.get('donor_name', '')
        donation.donor_email = request.POST.get('donor_email', '')
        donation.message = request.POST.get('message', '')
        donation.receipt_sent = request.POST.get('receipt_sent') == 'on'

        donation.save()

        return JsonResponse({
            'status': 'success',
            'message': _('Donation updated successfully.')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@require_POST
@login_required
def send_donation_receipt(request, pk):
    """Send receipt email for a donation"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({
            'status': 'error',
            'message': _('You do not have permission to send receipts.')
        })

    donation = get_object_or_404(Donation, pk=pk)

    try:
        # Check if donation has an email to send to
        if donation.is_anonymous and not donation.donor_email:
            return JsonResponse({
                'status': 'error',
                'message': _('Cannot send receipt: Donation is anonymous and has no email address.')
            })

        if not donation.donor and not donation.donor_email:
            return JsonResponse({
                'status': 'error',
                'message': _('Cannot send receipt: No donor email address available.')
            })

        # Import and use the email utility
        from .email_utils import send_donation_receipt_email
        
        # Send the receipt email
        success = send_donation_receipt_email(donation)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': _('Receipt sent successfully.')
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': _('Failed to send receipt email. Please check the email configuration.')
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@require_POST
@login_required
def update_campaign_status(request, pk):
    """Update campaign status"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({
            'status': 'error',
            'message': _('You do not have permission to update campaign status.')
        })

    campaign = get_object_or_404(Campaign, pk=pk)

    try:
        status = request.POST.get('status')
        if status and status in dict(Campaign._meta.get_field('status').choices):
            campaign.status = status
            campaign.save()

            return JsonResponse({
                'status': 'success',
                'message': _('Campaign status updated successfully.'),
                'new_status': dict(Campaign._meta.get_field('status').choices)[status]
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': _('Invalid status.')
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@require_POST
@login_required
def delete_campaign(request, pk):
    """Delete a campaign"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({
            'status': 'error',
            'message': _('You do not have permission to delete campaigns.')
        })

    campaign = get_object_or_404(Campaign, pk=pk)

    # Store campaign details before deletion
    campaign_id = campaign.id
    campaign_name = campaign.name
    donation_count = Donation.objects.filter(campaign=campaign).count()

    # Log campaign deletion warning
    logger.warning(
        f"Campaign deletion requested: Campaign ID={campaign_id}, Name={campaign_name}",
        extra={
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'donation_count': donation_count,
            'user_id': request.user.id,
            'action': 'campaign_deletion'
        }
    )

    try:
        # Check if campaign has donations
        if donation_count > 0:
            logger.warning(
                f"Campaign deletion blocked: Campaign has {donation_count} donations",
                extra={
                    'campaign_id': campaign_id,
                    'donation_count': donation_count,
                    'user_id': request.user.id
                }
            )
            return JsonResponse({
                'status': 'error',
                'message': _('Cannot delete campaign with existing donations.')
            })

        campaign.delete()
        
        # Log successful deletion
        logger.warning(
            f"Campaign deleted successfully: Campaign ID={campaign_id}, Name={campaign_name}",
            extra={
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'user_id': request.user.id,
                'action': 'campaign_deletion_complete'
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': _('Campaign deleted successfully.')
        })
    except Exception as e:
        logger.error(
            f"Error deleting campaign: {str(e)}",
            exc_info=True,
            extra={
                'campaign_id': campaign_id,
                'user_id': request.user.id,
                'error_type': type(e).__name__}
        )
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def campaign_create(request):
    """View to create a new campaign"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to create campaigns.'))
        return redirect('donations:campaign_list')

    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                campaign = form.save()
                
                # Log campaign creation
                logger.info(
                    f"Campaign created: Campaign ID={campaign.id}, Name={campaign.name}",
                    extra={
                        'campaign_id': campaign.id,
                        'campaign_name': campaign.name,
                        'campaign_slug': campaign.slug,
                        'goal_amount': float(campaign.goal_amount) if campaign.goal_amount else None,
                        'user_id': request.user.id,
                        'user_email': request.user.email
                    }
                )
                
                messages.success(request, _('Campaign created successfully!'))
                return redirect('donations:campaign_detail', slug=campaign.slug)
            except Exception as e:
                logger.error(
                    f"Error creating campaign: {str(e)}",
            exc_info=True,
            extra={
                        'user_id': request.user.id,
                        'error_type': type(e).__name__}
                )
                raise
    else:
        form = CampaignForm(user=request.user)

    context = {
        'form': form,
    }

    return render(request, 'donations/campaign_form.html', context)

@login_required
def campaign_edit(request, pk):
    """View to edit a campaign"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to edit campaigns.'))
        return redirect('donations:campaign_list')

    campaign = get_object_or_404(Campaign, pk=pk)

    if request.method == 'POST':
        # Store old values for comparison
        old_name = campaign.name
        old_status = campaign.status
        old_goal_amount = campaign.goal_amount
        
        form = CampaignForm(request.POST, request.FILES, instance=campaign, user=request.user)
        if form.is_valid():
            try:
                campaign = form.save()
                
                # Log changes
                changes = []
                if old_name != campaign.name:
                    changes.append(f"name: '{old_name}' -> '{campaign.name}'")
                if old_status != campaign.status:
                    changes.append(f"status: '{old_status}' -> '{campaign.status}'")
                if old_goal_amount != campaign.goal_amount:
                    changes.append(f"goal_amount: {old_goal_amount} -> {campaign.goal_amount}")
                
                # Log campaign update
                logger.info(
                    f"Campaign updated: Campaign ID={campaign.id}, Name={campaign.name}",
                    extra={
                        'campaign_id': campaign.id,
                        'campaign_name': campaign.name,
                        'campaign_slug': campaign.slug,
                        'user_id': request.user.id,
                        'changes': changes if changes else 'No changes detected'
                    }
                )
                
                messages.success(request, _('Campaign updated successfully!'))
                return redirect('donations:campaign_detail', slug=campaign.slug)
            except Exception as e:
                logger.error(
                    f"Error updating campaign: {str(e)}",
            exc_info=True,
            extra={
                        'campaign_id': campaign.id,
                        'user_id': request.user.id,
                        'error_type': type(e).__name__}
                )
                raise
    else:
        form = CampaignForm(instance=campaign, user=request.user)

    context = {
        'form': form,
        'campaign': campaign,
    }

    return render(request, 'donations/campaign_form.html', context)

@login_required
@transaction.atomic
def manage_gcash(request):
    """Staff-only UI to manage GCash configuration (single record)."""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')
    
    config = GCashConfig.get_active_config() or GCashConfig.objects.order_by('-updated_at').first()

    if request.method == 'POST':
        instance = config or GCashConfig()
        form = GCashConfigForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)

            # If activating, check for QR code
            if obj.is_active:
                if not obj.qr_code_image:
                    form.add_error('qr_code_image', _('QR code image is required to activate this configuration.'))
                    return render(request, 'donations/gcash_manage.html', {
                        'form': form,
                        'gcash_config': instance if instance.pk else None,
                    })

            obj.save()
            messages.success(request, _('GCash configuration saved successfully.'))
            return redirect('donations:manage_gcash')
    else:
        form = GCashConfigForm(instance=config)

    return render(request, 'donations/gcash_manage.html', {
        'form': form,
        'gcash_config': config,
    })


@require_GET
@never_cache
@ensure_csrf_cookie
def payment_instructions(request, pk):
    """Read-only instructions for the already-created amount and recipient."""
    donation = get_object_or_404(Donation.objects.select_related('campaign', 'campaign__gcash_config'), pk=pk)
    assert_donation_access(request, donation)
    if request.GET.get('access'):
        # Strip capability tokens from URL/history and avoid leaking in Referer.
        response = HttpResponseRedirect(reverse('donations:payment_instructions', kwargs={'pk': pk}))
        response['Referrer-Policy'] = DONATION_REFERRER_POLICY
        return response
    if donation.status != 'pending_payment':
        return redirect('donations:donation_confirmation', pk=pk)
    payment = payment_display(donation)
    if not payment['gcash_number'] or not payment['account_name']:
        messages.error(request, _('Payment details are unavailable. Contact the alumni office.'))
        return redirect('donations:donation_confirmation', pk=pk)
    # Render a signed, donation-scoped next-step link for guests. Their cache
    # session may be lost while they switch to GCash; never rely on IDs alone.
    guest_proof_claim = None
    if donation.donor_id is None:
        from .payment_flow import signed_guest_token
        guest_proof_claim = signed_guest_token(donation)
    context = {'donation': donation, 'payment': payment,
               'guest_proof_claim': guest_proof_claim}
    template = ('donations/donor_payment_guest.html' if not request.user.is_authenticated else
                'donations/donor_payment_staff.html' if can_manage_donations(request.user) else
                'donations/donor_payment.html')
    response = render(request, template, context)
    response['Referrer-Policy'] = DONATION_REFERRER_POLICY
    response['Cache-Control'] = 'private, no-store'
    return response


@never_cache
@ensure_csrf_cookie
def upload_payment_proof(request, pk):
    """Single validated endpoint for donor GCash evidence (never direct payment)."""
    donation = get_object_or_404(Donation, pk=pk)
    assert_donation_access(request, donation)
    if request.GET.get('access'):
        return redirect('donations:upload_payment_proof', pk=pk)
    if donation.status != 'pending_payment':
        return redirect('donations:donation_confirmation', pk=pk)
    form = PaymentProofForm(instance=donation)
    if request.method == 'POST':
        proof = None
        with transaction.atomic():
            locked = get_object_or_404(Donation.objects.select_for_update(), pk=pk)
            assert_donation_access(request, locked)
            if locked.status != 'pending_payment':
                return redirect('donations:donation_confirmation', pk=pk)
            # Bind the POST and uploaded file directly to the locked instance.
            # Replacing form.instance after is_valid() discards the validated
            # reference_number and payment_proof while advancing the status.
            form = PaymentProofForm(request.POST, request.FILES, instance=locked)
            if form.is_valid():
                proof = form.save(commit=False)
                proof.status = 'pending_verification'
                proof.save()
        if proof is not None:
            # Fraud detection is advisory; verification still requires staff review.
            try:
                from .fraud_detection import fraud_detector
                fraud_detector.analyze_donation(proof, request)
            except Exception:
                logger.exception('Fraud screening unavailable for donation %s', pk)
            message = _('Payment proof submitted. Your donation is awaiting manual verification; no payment has been confirmed yet.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': str(message), 'redirect_url': reverse('donations:donation_confirmation', kwargs={'pk': pk})})
            messages.success(request, message)
            return redirect('donations:donation_confirmation', pk=pk)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Please correct the proof fields.', 'errors': form.errors}, status=400)
    template = ('donations/donor_proof_guest.html' if not request.user.is_authenticated else
                'donations/donor_proof_staff.html' if can_manage_donations(request.user) else
                'donations/donor_proof.html')
    # This capability is only placed in a rendered form after ownership has
    # already been checked. Registered donors must still authenticate.
    guest_proof_claim = None
    if donation.donor_id is None:
        from .payment_flow import signed_guest_token
        guest_proof_claim = signed_guest_token(donation)
    response = render(request, template, {
        'donation': donation, 'form': form, 'guest_proof_claim': guest_proof_claim,
    })
    response['Cache-Control'] = 'private, no-store'
    response['Referrer-Policy'] = DONATION_REFERRER_POLICY
    return response


@login_required
@require_GET
@never_cache
def view_payment_proof(request, pk):
    """Admin/coordinator-only download; new files use private storage."""
    if not can_manage_donations(request.user):
        raise PermissionDenied
    donation = get_object_or_404(Donation, pk=pk)
    if not donation.payment_proof:
        raise Http404
    try:
        file_handle = donation.payment_proof.open('rb')
    except (OSError, FileNotFoundError):
        raise Http404
    import mimetypes
    mime_type = mimetypes.guess_type(donation.payment_proof.name)[0] or 'application/octet-stream'
    response = FileResponse(file_handle, content_type=mime_type)
    response['Content-Disposition'] = 'inline; filename="donation-proof"'
    response['Cache-Control'] = 'no-store, private'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
def verification_dashboard(request):
    """Enhanced admin dashboard for verifying donations"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    # Get filter parameters
    tab = request.GET.get('tab', 'pending')
    search = request.GET.get('search', '')
    campaign_filter = request.GET.get('campaign', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    sort_by = request.GET.get('sort', '-created_at')

    # Base queryset
    donations = Donation.objects.select_related('campaign', 'donor', 'verified_by')

    # Apply tab filter
    if tab == 'pending':
        donations = donations.filter(status='pending_verification')
    elif tab == 'completed':
        donations = donations.filter(status='completed')
    elif tab == 'failed':
        donations = donations.filter(status='failed')
    elif tab == 'disputed':
        donations = donations.filter(status='disputed')
    elif tab == 'all':
        donations = donations.exclude(status='pending_payment')

    # Apply search filter
    if search:
        donations = donations.filter(
            Q(donor__first_name__icontains=search) |
            Q(donor__last_name__icontains=search) |
            Q(donor__email__icontains=search) |
            Q(donor_name__icontains=search) |
            Q(donor_email__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(gcash_transaction_id__icontains=search) |
            Q(campaign__name__icontains=search)
        )

    # Apply campaign filter
    if campaign_filter:
        donations = donations.filter(campaign_id=campaign_filter)

    # Apply date range filter
    if date_from:
        try:
            date_from_parsed = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            donations = donations.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_parsed = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            donations = donations.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass

    # Apply sorting
    valid_sorts = ['-created_at', 'created_at', '-amount', 'amount', '-verification_date', 'verification_date']
    if sort_by in valid_sorts:
        donations = donations.order_by(sort_by)
    else:
        donations = donations.order_by('-created_at')

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(donations, 25)  # 25 donations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics for all tabs
    stats = {
        'pending_count': Donation.objects.filter(status='pending_verification').count(),
        'completed_count': Donation.objects.filter(status='completed').count(),
        'failed_count': Donation.objects.filter(status='failed').count(),
        'disputed_count': Donation.objects.filter(status='disputed').count(),
        'today_verified': Donation.objects.filter(
            verification_date__date=timezone.now().date()
        ).count(),
        'total_verified': Donation.objects.filter(
            status='completed'
        ).count(),
    }

    # Get campaigns for filter dropdown
    campaigns = Campaign.objects.filter(status='active').order_by('name')

    # Admin performance metrics
    admin_stats = None
    if request.user.is_superuser:
        from django.db.models import Count, Avg
        admin_stats = User.objects.filter(
            verified_donations__verification_date__date=timezone.now().date()
        ).annotate(
            verifications_today=Count('verified_donations'),
            avg_verification_time=Avg('verified_donations__verification_date')
        ).order_by('-verifications_today')[:5]

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'campaigns': campaigns,
        'admin_stats': admin_stats,
        'current_tab': tab,
        'search': search,
        'campaign_filter': campaign_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
    }

    return render(request, 'donations/verification_dashboard.html', context)


@login_required
@require_POST
def verify_donation(request, pk):
    """Manual review of a received GCash transaction (staff-only)."""
    if not can_manage_donations(request.user):
        return JsonResponse({'status': 'error', 'message': _('Permission denied.')}, status=403)
    with transaction.atomic():
        donation = get_object_or_404(Donation.objects.select_for_update(), pk=pk)
        if donation.status != 'pending_verification':
            return JsonResponse({'status': 'error', 'message': 'Donation is no longer awaiting verification.'}, status=409)
        form = DonationVerificationForm(request.POST, instance=donation)
        if not form.is_valid():
            return JsonResponse({'status': 'error', 'message': _('Invalid verification data.'), 'errors': form.errors}, status=400)
        result = form.save(commit=False)
        if result.status == 'completed' and request.POST.get('gcash_reconciled') != 'yes':
            return JsonResponse({'status': 'error', 'message': 'Confirm the actual GCash credit before approval.'}, status=400)
        if result.status == 'completed' and (not donation.payment_proof or not donation.reference_number):
            return JsonResponse({'status': 'error', 'message': 'Cannot approve without receipt proof and reference number.'}, status=400)
        result.verified_by = request.user
        result.verification_date = timezone.now()
        result.save()
    logger.info('Donation %s reviewed with status %s by staff %s', pk, result.status, request.user.pk)
    return JsonResponse({'status': 'success', 'message': _('Donation review recorded.'), 'new_status': result.get_status_display()})


@login_required
@require_POST
def bulk_verify_donations(request):
    """Bulk verification of donations"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'})

    try:
        import json
        action = request.POST.get('action')
        donation_ids = json.loads(request.POST.get('donation_ids', '[]'))
        notes = request.POST.get('notes', '')

        # Log bulk operation start
        logger.info(
            f"Bulk donation verification started: Action={action}, Count={len(donation_ids)}",
            extra={
                'action': action,
                'donation_ids': donation_ids,
                'donation_count': len(donation_ids),
                'user_id': request.user.id
            }
        )

        if not action or not donation_ids:
            return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})

        if action not in ['completed', 'failed', 'disputed']:
            return JsonResponse({'status': 'error', 'message': 'Invalid action'})
        if action == 'completed' and request.POST.get('gcash_reconciled') != 'yes':
            return JsonResponse({'status': 'error', 'message': 'Confirm actual GCash receipts before bulk approval.'}, status=400)

        processed_count = 0
        skipped_count = 0
        with transaction.atomic():
            donations = Donation.objects.select_for_update().filter(
                id__in=donation_ids, status='pending_verification')
            for donation in donations:
                if action == 'completed' and (not donation.payment_proof or not donation.reference_number):
                    skipped_count += 1
                    continue
                donation.status = action
                donation.verified_by = request.user
                donation.verification_date = timezone.now()
                if notes:
                    donation.verification_notes = notes
                donation.save()
                processed_count += 1

        # Log bulk operation completion
        logger.info(
            f"Bulk donation verification completed: Action={action}, Processed={processed_count}",
            extra={
                'action': action,
                'processed_count': processed_count,
                'requested_count': len(donation_ids),
                'user_id': request.user.id
            }
        )

        return JsonResponse({
            'status': 'success',
            'processed_count': processed_count,
            'skipped_count': skipped_count,
            'message': f'Processed {processed_count} donations; {skipped_count} missing receipt proof or reference'
        })

    except Exception as e:
        logger.error(
            f"Error in bulk donation verification: {str(e)}",
            exc_info=True,
            extra={
                'action': request.POST.get('action'),
                'user_id': request.user.id,
                'error_type': type(e).__name__}
        )
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def export_donations(request):
    """Export donations data to CSV"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    import csv
    from django.http import HttpResponse

    # Get filter parameters (same as verification dashboard)
    tab = request.GET.get('tab', 'all')
    search = request.GET.get('search', '')
    campaign_filter = request.GET.get('campaign', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Base queryset
    donations = Donation.objects.select_related('campaign', 'donor', 'verified_by')

    # Apply filters (same logic as verification dashboard)
    if tab != 'all':
        if tab == 'pending':
            donations = donations.filter(status='pending_verification')
        elif tab == 'completed':
            donations = donations.filter(status='completed')
        elif tab == 'failed':
            donations = donations.filter(status='failed')
        elif tab == 'disputed':
            donations = donations.filter(status='disputed')
    else:
        donations = donations.exclude(status='pending_payment')

    # Apply search and other filters
    if search:
        donations = donations.filter(
            Q(donor__first_name__icontains=search) |
            Q(donor__last_name__icontains=search) |
            Q(donor__email__icontains=search) |
            Q(donor_name__icontains=search) |
            Q(donor_email__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(gcash_transaction_id__icontains=search) |
            Q(campaign__name__icontains=search)
        )

    if campaign_filter:
        donations = donations.filter(campaign_id=campaign_filter)

    if date_from:
        try:
            date_from_parsed = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            donations = donations.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_parsed = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            donations = donations.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="donations_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Reference Number',
        'Donor Name',
        'Donor Email',
        'Campaign',
        'Amount',
        'Status',
        'Payment Method',
        'GCash Transaction ID',
        'Created Date',
        'Verification Date',
        'Verified By',
        'Verification Notes',
        'Is Anonymous'
    ])

    for donation in donations.order_by('-created_at'):
        donor_name = 'Anonymous' if donation.is_anonymous else (
            donation.donor.get_full_name() if donation.donor else donation.donor_name
        )
        donor_email = '' if donation.is_anonymous else (
            donation.donor.email if donation.donor else donation.donor_email
        )

        writer.writerow([
            donation.reference_number,
            donor_name,
            donor_email,
            donation.campaign.name,
            donation.amount,
            donation.get_status_display(),
            'GCash',
            donation.gcash_transaction_id or '',
            donation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            donation.verification_date.strftime('%Y-%m-%d %H:%M:%S') if donation.verification_date else '',
            donation.verified_by.get_full_name() if donation.verified_by else '',
            donation.verification_notes or '',
            'Yes' if donation.is_anonymous else 'No'
        ])

    return response


@login_required
def analytics_dashboard(request):
    """Advanced analytics dashboard for donations"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DurationField
    from django.db.models.functions import TruncDay, TruncMonth
    from django.db.models import Q
    import json
    from datetime import timedelta, datetime

    # Date range filter - use datetime for proper filtering
    # Since USE_TZ is False, we need to use naive datetimes for MySQL
    try:
        days = int(request.GET.get('days', 30))
    except (ValueError, TypeError):
        days = 30
    
    # Use naive datetime for MySQL compatibility when USE_TZ is False
    # Use datetime.now() directly to ensure naive datetime
    from datetime import datetime as dt
    now = dt.now()
    
    end_datetime = now
    start_datetime = end_datetime - timedelta(days=days)
    start_date = start_datetime.date()
    end_date = end_datetime.date()

    # Basic statistics - all time completed donations
    total_donations = Donation.objects.filter(status='completed').aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id'),
        avg_amount=Avg('amount')
    )

    # Daily donation trends - use TruncDay for proper date grouping
    # Note: TruncDay might not work in all databases, so we'll use a more compatible approach
    daily_trends_queryset = Donation.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime,
        status='completed'
    )
    
    # Debug: Log count of donations found
    donation_count = daily_trends_queryset.count()
    print(f"DEBUG: Found {donation_count} completed donations in date range {start_date} to {end_date}")
    print(f"DEBUG: Start datetime: {start_datetime}, End datetime: {end_datetime}")
    
    # Also check all completed donations to see what we're working with
    all_completed = Donation.objects.filter(status='completed')
    print(f"DEBUG: Total completed donations (all time): {all_completed.count()}")
    for d in all_completed[:5]:  # Show first 5
        print(f"  - ID: {d.id}, Amount: {d.amount}, Created: {d.created_at}, Status: {d.status}")
    
    # Group by date using TruncDay if available, otherwise use extra
    try:
        daily_trends = daily_trends_queryset.annotate(
            day=TruncDay('created_at')
    ).values('day').annotate(
        amount=Sum('amount'),
        count=Count('id')
    ).order_by('day')
        print(f"DEBUG: Using TruncDay for daily trends")
    except Exception as e:
        # Fallback for databases that don't support TruncDay
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"TruncDay not supported, using extra: {e}")
        daily_trends = daily_trends_queryset.extra(
            select={'day': "DATE(created_at)"}
        ).values('day').annotate(
            amount=Sum('amount'),
            count=Count('id')
        ).order_by('day')
        print(f"DEBUG: Using extra() for daily trends")
    
    # Debug: Log the daily trends data
    daily_trends_list = list(daily_trends)
    print(f"DEBUG: Daily trends query result: {daily_trends_list}")

    # Campaign performance - filter by date range for more accurate results
    campaign_performance = Campaign.objects.annotate(
        total_raised=Sum('donations__amount', filter=Q(
            donations__status='completed',
            donations__created_at__gte=start_datetime,
            donations__created_at__lte=end_datetime
        )),
        donation_count=Count('donations', filter=Q(
            donations__status='completed',
            donations__created_at__gte=start_datetime,
            donations__created_at__lte=end_datetime
        )),
        avg_donation=Avg('donations__amount', filter=Q(
            donations__status='completed',
            donations__created_at__gte=start_datetime,
            donations__created_at__lte=end_datetime
        ))
    ).filter(total_raised__isnull=False, total_raised__gt=0).order_by('-total_raised')[:10]

    # Verification efficiency - calculate average verification time properly
    # Use naive datetime for MySQL compatibility
    verified_donations = Donation.objects.filter(
        verification_date__isnull=False,
        verification_date__gte=start_datetime,
        verification_date__lte=end_datetime,
        status__in=['completed', 'failed', 'disputed']
    )
    
    # Calculate average verification time in hours
    verification_times = []
    for donation in verified_donations:
        if donation.verification_date and donation.created_at:
            time_diff = donation.verification_date - donation.created_at
            verification_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
    
    avg_verification_hours = sum(verification_times) / len(verification_times) if verification_times else 0
    
    verification_stats = {
        'avg_verification_time': avg_verification_hours,
        'total_verified': verified_donations.count()
    }

    # Payment method breakdown - all donations are GCash
    payment_methods_data = Donation.objects.filter(
        status='completed',
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id')
    )
    
    print(f"DEBUG: Payment methods data - total_amount: {payment_methods_data['total_amount']}, total_count: {payment_methods_data['total_count']}")
    print(f"DEBUG: Payment methods data type - total_amount type: {type(payment_methods_data['total_amount'])}, total_count type: {type(payment_methods_data['total_count'])}")
    
    # Since all donations are GCash, create a single entry
    # Always create an entry even if count is 0, so the chart shows something
    payment_amount_value = float(payment_methods_data['total_amount'] or 0)
    payment_count_value = int(payment_methods_data['total_count'] or 0)
    print(f"DEBUG: Payment method values - amount: {payment_amount_value}, count: {payment_count_value}")
    
    payment_methods = [{
        'payment_method': 'GCash',
        'amount': payment_amount_value,
        'count': payment_count_value
    }]

    # Admin performance - use correct related_name and filter by date range
    admin_performance = User.objects.filter(
        verified_donations__verification_date__gte=start_datetime,
        verified_donations__verification_date__lte=end_datetime
    ).annotate(
        verifications=Count('verified_donations', filter=Q(
            verified_donations__verification_date__gte=start_datetime,
            verified_donations__verification_date__lte=end_datetime
        )),
        total_amount=Sum('verified_donations__amount', filter=Q(
            verified_donations__verification_date__gte=start_datetime,
            verified_donations__verification_date__lte=end_datetime,
            verified_donations__status='completed'
        ))
    ).filter(verifications__gt=0).order_by('-verifications')[:10]

    # Monthly trends for charts - use longer range for better visualization
    monthly_start_date = end_date - timedelta(days=365)
    # Use naive datetime for MySQL compatibility
    monthly_start_datetime = dt.combine(monthly_start_date, dt.min.time())
    
    monthly_trends = Donation.objects.filter(
        status='completed',
        created_at__gte=monthly_start_datetime,
        created_at__lte=end_datetime
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        amount=Sum('amount'),
        count=Count('id')
    ).order_by('month')

    # Prepare chart data - ensure all data is properly formatted
    # Handle empty data gracefully
    daily_labels = []
    daily_amounts = []
    daily_counts = []
    
    # Convert queryset to list for debugging
    daily_trends_list = list(daily_trends) if daily_trends else []
    print(f"DEBUG: Processing {len(daily_trends_list)} daily trend items")
    
    if daily_trends_list:
        for item in daily_trends_list:
            day = item.get('day')
            amount = item.get('amount') or 0
            count = item.get('count') or 0
            
            print(f"DEBUG: Processing item - day: {day}, amount: {amount}, count: {count}")
            
            if day:
                # Handle both date objects and date strings
                if isinstance(day, str):
                    # Parse date string (format: YYYY-MM-DD)
                    try:
                        from datetime import datetime as dt
                        day_obj = dt.strptime(day, '%Y-%m-%d').date()
                        daily_labels.append(day_obj.strftime('%Y-%m-%d'))
                    except (ValueError, AttributeError):
                        daily_labels.append(str(day)[:10])  # Take first 10 chars (YYYY-MM-DD)
                elif hasattr(day, 'strftime'):
                    daily_labels.append(day.strftime('%Y-%m-%d'))
                else:
                    daily_labels.append(str(day)[:10])
                
                daily_amounts.append(float(amount))
                daily_counts.append(int(count))
    
    print(f"DEBUG: Final daily data - Labels: {len(daily_labels)}, Amounts: {len(daily_amounts)}, Counts: {len(daily_counts)}")
    
    monthly_labels = []
    monthly_amounts = []
    
    if monthly_trends:
        for item in monthly_trends:
            if item.get('month'):
                monthly_labels.append(item['month'].strftime('%Y-%m'))
                monthly_amounts.append(float(item.get('amount') or 0))
    
    payment_labels = []
    payment_amounts = []
    payment_counts = []
    
    if payment_methods:
        for item in payment_methods:
            payment_labels.append(item.get('payment_method', 'GCash'))
            payment_amounts.append(float(item.get('amount') or 0))
            payment_counts.append(item.get('count') or 0)
    
    chart_data = {
        'daily_amounts': daily_amounts,
        'daily_counts': daily_counts,
        'daily_labels': daily_labels,
        'monthly_amounts': monthly_amounts,
        'monthly_labels': monthly_labels,
        'payment_methods': {
            'labels': payment_labels if payment_labels else ['GCash'],
            'amounts': payment_amounts if payment_amounts else [0],
            'counts': payment_counts if payment_counts else [0]
        }
    }
    
    # Debug: Print final chart data structure
    print(f"DEBUG: Final chart_data structure:")
    print(f"  - daily_labels: {len(chart_data['daily_labels'])} items - {chart_data['daily_labels']}")
    print(f"  - daily_amounts: {len(chart_data['daily_amounts'])} items - {chart_data['daily_amounts']}")
    print(f"  - payment_methods.labels: {chart_data['payment_methods']['labels']}")
    print(f"  - payment_methods.amounts: {chart_data['payment_methods']['amounts']}")

    context = {
        'total_donations': total_donations,
        'campaign_performance': campaign_performance,
        'verification_stats': verification_stats,
                'admin_performance': admin_performance,
        'chart_data': json.dumps(chart_data),
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'donations/analytics_dashboard.html', context)


@login_required
def fraud_monitoring_dashboard(request):
    """Fraud monitoring dashboard for admins"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    from .fraud_detection import fraud_detector
    from .models import FraudAlert, BlacklistedEntity

    # Get fraud summary
    days = int(request.GET.get('days', 30))
    
    # Log dashboard access
    logger.info(
        f"Fraud monitoring dashboard accessed: Days={days}",
        extra={
            'user_id': request.user.id,
            'days': days,
            'action': 'fraud_dashboard_access'
        }
    )
    
    fraud_summary = fraud_detector.get_fraud_summary(days)

    # Get recent alerts
    recent_alerts = FraudAlert.objects.select_related(
        'donation', 'donation__campaign', 'reviewed_by'
    ).order_by('-created_at')[:20]

    # Get pending alerts
    pending_alerts = FraudAlert.objects.filter(
        status='pending'
    ).select_related('donation', 'donation__campaign').order_by('-severity', '-created_at')

    # Get high-risk donations
    high_risk_donations = Donation.objects.filter(
        fraud_alerts__severity__in=['high', 'critical'],
        fraud_alerts__status='pending'
    ).distinct().select_related('campaign')

    # Get blacklisted entities
    blacklisted_entities = BlacklistedEntity.objects.filter(
        is_active=True
    ).order_by('-created_at')[:10]

    context = {
        'fraud_summary': fraud_summary,
        'recent_alerts': recent_alerts,
        'pending_alerts': pending_alerts,
        'high_risk_donations': high_risk_donations,
        'blacklisted_entities': blacklisted_entities,
        'days': days,
    }

    return render(request, 'donations/fraud_monitoring_dashboard.html', context)


@login_required
@require_POST
def resolve_fraud_alert(request, alert_id):
    """Resolve a fraud alert"""
    # Check if user is staff, admin, or alumni coordinator
    if not can_manage_donations(request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'})

    from .models import FraudAlert
    alert = get_object_or_404(FraudAlert, id=alert_id)

    status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    if status not in ['resolved', 'false_positive', 'investigating']:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'})

    alert.status = status
    alert.resolution_notes = notes
    alert.reviewed_by = request.user
    alert.reviewed_at = timezone.now()
    alert.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Alert resolved successfully'
    })

@login_required
def manage_gcash(request):
    """List all GCash configurations (staff only)"""
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    # Get all GCash configurations
    gcash_configs = GCashConfig.objects.all().order_by('-is_active', '-created_at')
    
    # Get statistics
    total_configs = gcash_configs.count()
    active_configs = gcash_configs.filter(is_active=True).count()
    inactive_configs = gcash_configs.filter(is_active=False).count()
    
    # Get campaigns using each config
    config_usage = {}
    for config in gcash_configs:
        config_usage[config.id] = config.campaigns.count()

    # Add usage count to each config object
    for config in gcash_configs:
        config.usage_count = config_usage.get(config.id, 0)

    context = {
        'gcash_configs': gcash_configs,
        'total_configs': total_configs,
        'active_configs': active_configs,
        'inactive_configs': inactive_configs,
        'config_usage': config_usage,
    }
    return render(request, 'donations/gcash_list.html', context)

@login_required
def gcash_config_detail(request, pk):
    """View/edit specific GCash configuration (staff only)"""
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:manage_gcash')

    config = get_object_or_404(GCashConfig, pk=pk)
    
    if request.method == 'POST':
        form = GCashConfigForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            config = form.save()
            messages.success(request, _('GCash configuration updated successfully.'))
            return redirect('donations:manage_gcash')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = GCashConfigForm(instance=config)

    # Get campaigns using this config
    campaigns_using = config.campaigns.all()

    context = {
        'form': form,
        'config': config,
        'campaigns_using': campaigns_using,
    }
    return render(request, 'donations/gcash_config_detail.html', context)

@login_required
def gcash_config_create(request):
    """Create new GCash configuration (staff only)"""
    if not can_manage_donations(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:manage_gcash')

    if request.method == 'POST':
        form = GCashConfigForm(request.POST, request.FILES)
        if form.is_valid():
            config = form.save()
            messages.success(request, _('GCash configuration created successfully.'))
            return redirect('donations:manage_gcash')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = GCashConfigForm()

    context = {
        'form': form,
    }
    return render(request, 'donations/gcash_config_form.html', context)

@login_required
@require_POST
def toggle_gcash_config(request, pk):
    """Toggle GCash configuration active status (staff only)"""
    if not can_manage_donations(request.user):
        return JsonResponse({'status': 'error', 'message': _('Permission denied')}, status=403)

    config = get_object_or_404(GCashConfig, pk=pk)
    
    try:
        import json
        data = json.loads(request.body)
        is_active = data.get('is_active', False)
        
        # If activating, check for QR code
        if is_active:
            # Check if QR code exists
            if not config.qr_code_image:
                return JsonResponse({
                    'status': 'error',
                    'message': _('QR code image is required to activate this configuration.')
                }, status=400)
        
        config.is_active = is_active
        config.save()
        
        status_text = _('activated') if is_active else _('deactivated')
        return JsonResponse({
            'status': 'success',
            'message': _('Configuration {} successfully.').format(status_text),
            'is_active': config.is_active
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': _('Invalid request data.')
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def donation_faq(request):
    """View to display donation FAQ and help documentation"""
    context = {
        'gcash_config': GCashConfig.get_active_config(),
    }
    return render(request, 'donations/donation_faq.html', context)
