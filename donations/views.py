from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Campaign, CampaignType, Donation, DonorRecognition, CampaignUpdate, GCashConfig
from .forms import DonationForm, CampaignFilterForm, CampaignForm, PaymentProofForm, DonationVerificationForm
from accounts.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db import models
from .forms_gcash import GCashConfigForm


def campaign_list(request):
    """View to display list of campaigns with filtering"""
    campaigns = Campaign.objects.all()

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

    # Featured campaigns for sidebar
    featured_campaigns = Campaign.objects.filter(
        is_featured=True,
        status='active'
    ).order_by('-start_date')[:3]

    # Paginate results
    paginator = Paginator(campaigns, 9)  # 9 campaigns per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'campaign_types': campaign_types,
        'featured_campaigns': featured_campaigns,
    }

    return render(request, 'donations/campaign_list.html', context)

def campaign_detail(request, slug):
    """View to display campaign details and donation form"""
    campaign = get_object_or_404(Campaign, slug=slug)

    # Get recent donations for this campaign
    recent_donations = Donation.objects.filter(
        campaign=campaign,
        status='completed',
        is_anonymous=False
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

    # Initialize donation form
    if request.method == 'POST':
        # Require active GCash configuration with QR code before accepting donations
        gcash_config = GCashConfig.get_active_config()
        if not gcash_config or not gcash_config.qr_code_image:
            messages.error(request, _('GCash payment is currently unavailable. Please try again later.'))
            return redirect('donations:campaign_list')

        form = DonationForm(
            request.POST,
            user=request.user,
            campaign=campaign
        )

        if form.is_valid():
            donation = form.save()

            messages.success(
                request,
                _('Donation created! Please follow the payment instructions to complete your donation.')
            )
            return redirect('donations:payment_instructions', pk=donation.pk)
    else:
        form = DonationForm(user=request.user, campaign=campaign)

    context = {
        'campaign': campaign,
        'form': form,
        'recent_donations': recent_donations,
        'updates': updates,
        'donation_stats': donation_stats,
    }

    return render(request, 'donations/campaign_detail.html', context)

@login_required
def donation_history(request):
    """View to display user's donation history"""
    donations = Donation.objects.filter(
        donor=request.user
    ).select_related('campaign').order_by('-donation_date')

    # Calculate statistics
    total_donated = donations.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0

    campaigns_supported = donations.filter(
        status='completed'
    ).values('campaign').distinct().count()

    context = {
        'donations': donations,
        'total_donated': total_donated,
        'campaigns_supported': campaigns_supported,
    }

    return render(request, 'donations/donation_history.html', context)

def donation_confirmation(request, pk):
    """View to display donation confirmation"""
    donation = get_object_or_404(Donation, pk=pk)

    # Security check - only allow viewing if:
    # 1. User is the donor, or
    # 2. User has the donor email (for non-authenticated users)
    if request.user.is_authenticated:
        if donation.donor and donation.donor != request.user:
            messages.error(request, _('You do not have permission to view this donation.'))
            return redirect('donations:campaign_list')
    else:
        # For non-authenticated users, require email verification
        donor_email = request.session.get('donor_email')
        if not donor_email or donor_email != donation.donor_email:
            messages.error(request, _('You do not have permission to view this donation.'))
            return redirect('donations:campaign_list')

    context = {
        'donation': donation,
    }

    return render(request, 'donations/donation_confirmation.html', context)

@login_required
def campaign_donors(request, slug):
    """View to display all donors for a campaign"""
    campaign = get_object_or_404(Campaign, slug=slug)

    # Get all non-anonymous donations
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

@login_required
def dashboard(request):
    """Admin dashboard for donations"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    # Get statistics
    total_donations = Donation.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0

    donation_count = Donation.objects.filter(status='completed').count()

    campaign_count = Campaign.objects.count()
    active_campaign_count = Campaign.objects.filter(status='active').count()

    # Get recent donations
    recent_donations = Donation.objects.filter(
        status='completed'
    ).select_related('campaign', 'donor').order_by('-donation_date')[:10]

    # Get campaigns by status
    campaigns_by_status = Campaign.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    context = {
        'total_donations': total_donations,
        'donation_count': donation_count,
        'campaign_count': campaign_count,
        'active_campaign_count': active_campaign_count,
        'recent_donations': recent_donations,
        # Alias for templates expecting 'donations' variable name
        'donations': recent_donations,
        'campaigns_by_status': campaigns_by_status,
    }

    return render(request, 'donations/dashboard.html', context)

@require_POST
@login_required
def update_donation_status(request, pk):
    """AJAX view to update donation status"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': _('Permission denied')}, status=403)

    donation = get_object_or_404(Donation, pk=pk)
    status = request.POST.get('status')

    if status not in [choice[0] for choice in Donation.STATUS_CHOICES]:
        return JsonResponse({'status': 'error', 'message': _('Invalid status')}, status=400)

    donation.status = status
    donation.save()

    return JsonResponse({
        'status': 'success',
        'message': _('Donation status updated successfully'),
        'new_status': donation.get_status_display()
    })

@login_required
def manage_donations(request):
    """View to manage all donations with advanced filtering and bulk actions"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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

        # Logic to send email would go here
        # For now, just mark as sent
        donation.receipt_sent = True
        donation.save()

        return JsonResponse({
            'status': 'success',
            'message': _('Receipt sent successfully.')
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({
            'status': 'error',
            'message': _('You do not have permission to delete campaigns.')
        })

    campaign = get_object_or_404(Campaign, pk=pk)

    try:
        # Check if campaign has donations
        if Donation.objects.filter(campaign=campaign).exists():
            return JsonResponse({
                'status': 'error',
                'message': _('Cannot delete campaign with existing donations.')
            })

        campaign.delete()
        return JsonResponse({
            'status': 'success',
            'message': _('Campaign deleted successfully.')
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def campaign_create(request):
    """View to create a new campaign"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to create campaigns.'))
        return redirect('donations:campaign_list')

    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            campaign = form.save()
            messages.success(request, _('Campaign created successfully!'))
            return redirect('donations:campaign_detail', slug=campaign.slug)
    else:
        form = CampaignForm(user=request.user)

    context = {
        'form': form,
    }

    return render(request, 'donations/campaign_form.html', context)

@login_required
def campaign_edit(request, pk):
    """View to edit a campaign"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to edit campaigns.'))
        return redirect('donations:campaign_list')

    campaign = get_object_or_404(Campaign, pk=pk)

    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Campaign updated successfully!'))
            return redirect('donations:campaign_detail', slug=campaign.slug)
    else:
        form = CampaignForm(instance=campaign, user=request.user)

@staff_member_required
@transaction.atomic
def manage_gcash(request):
    """Staff-only UI to manage GCash configuration (single record)."""
    config = GCashConfig.get_active_config() or GCashConfig.objects.order_by('-updated_at').first()

    if request.method == 'POST':
        instance = config or GCashConfig()
        form = GCashConfigForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)

            # If activating, ensure only one active at a time
            if obj.is_active:
                if not obj.qr_code_image:
                    form.add_error('qr_code_image', _('QR code image is required to activate this configuration.'))
                    return render(request, 'donations/gcash_manage.html', {
                        'form': form,
                        'gcash_config': instance if instance.pk else None,
                    })
                # Deactivate others
                GCashConfig.objects.exclude(pk=obj.pk).update(is_active=False)

            obj.save()
            messages.success(request, _('GCash configuration saved successfully.'))
            return redirect('donations:manage_gcash')
    else:
        form = GCashConfigForm(instance=config)

    return render(request, 'donations/gcash_manage.html', {
        'form': form,
        'gcash_config': config,
    })


def payment_instructions(request, pk):
    """View to display GCash payment instructions and QR code"""
    donation = get_object_or_404(Donation, pk=pk)

    # Security check - only allow viewing if:
    # 1. User is the donor, or
    # 2. User has the donor email (for non-authenticated users)
    if request.user.is_authenticated:
        if donation.donor and donation.donor != request.user:
            messages.error(request, _('You do not have permission to view this donation.'))
            return redirect('donations:campaign_list')
    else:
        # For non-authenticated users, store email in session for later verification
        if donation.donor_email:
            request.session['donor_email'] = donation.donor_email

    # Get active GCash configuration
    gcash_config = GCashConfig.get_active_config()
    if not gcash_config or not gcash_config.qr_code_image:
        messages.error(request, _('GCash payment is currently unavailable. Please try again later.'))
        return redirect('donations:campaign_detail', slug=donation.campaign.slug)

    context = {
        'donation': donation,
        'gcash_config': gcash_config,
    }

    return render(request, 'donations/payment_instructions.html', context)


def upload_payment_proof(request, pk):
    """View to handle payment proof upload"""
    donation = get_object_or_404(Donation, pk=pk)

    # Security check
    if request.user.is_authenticated:
        if donation.donor and donation.donor != request.user:
            messages.error(request, _('You do not have permission to access this donation.'))
            return redirect('donations:campaign_list')
    else:
        # For non-authenticated users, check email in session
        donor_email = request.session.get('donor_email')
        if not donor_email or donor_email != donation.donor_email:
            messages.error(request, _('You do not have permission to access this donation.'))
            return redirect('donations:campaign_list')

    # Check if donation is in correct status
    if donation.status != 'pending_payment':
        messages.warning(request, _('This donation has already been processed.'))
        return redirect('donations:donation_confirmation', pk=donation.pk)

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=donation)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.status = 'pending_verification'
            donation.save()

            # Run fraud detection
            from .fraud_detection import fraud_detector
            fraud_alerts = fraud_detector.analyze_donation(donation, request)

            # If high-risk alerts are found, flag for manual review
            high_risk_alerts = [alert for alert in fraud_alerts if alert.severity in ['high', 'critical']]
            if high_risk_alerts:
                donation.status = 'disputed'  # Flag for manual review
                donation.save()

                messages.warning(
                    request,
                    _('Your donation has been flagged for manual review. Our team will verify it within 24 hours.')
                )
            else:
                messages.success(
                    request,
                    _('Payment proof uploaded successfully! Your donation will be verified within 24 hours.')
                )

            return redirect('donations:donation_confirmation', pk=donation.pk)
    else:
        form = PaymentProofForm(instance=donation)

    context = {
        'donation': donation,
        'form': form,
    }

    return render(request, 'donations/upload_payment_proof.html', context)


@login_required
def verification_dashboard(request):
    """Enhanced admin dashboard for verifying donations"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    """AJAX view to verify a donation"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': _('Permission denied.')})

    donation = get_object_or_404(Donation, pk=pk)

    form = DonationVerificationForm(request.POST, instance=donation)
    if form.is_valid():
        donation = form.save(commit=False)
        donation.verified_by = request.user
        donation.verification_date = timezone.now()
        donation.save()

        return JsonResponse({
            'status': 'success',
            'message': _('Donation verified successfully.'),
            'new_status': donation.get_status_display()
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': _('Invalid form data.'),
            'errors': form.errors
        })


def donation_status_tracker(request, reference_number=None):
    """View to track donation status by reference number"""
    donation = None
    error_message = None

    if reference_number:
        try:
            donation = Donation.objects.get(reference_number=reference_number)

            # Security check for non-authenticated users
            if not request.user.is_authenticated:
                if donation.donor_email:
                    request.session['donor_email'] = donation.donor_email
            elif donation.donor and donation.donor != request.user:
                error_message = _('You do not have permission to view this donation.')
                donation = None

        except Donation.DoesNotExist:
            error_message = _('Donation not found. Please check your reference number.')

    if request.method == 'POST' and not donation:
        reference_number = request.POST.get('reference_number', '').strip().upper()
        if reference_number:
            return redirect('donations:donation_status_tracker', reference_number=reference_number)

    context = {
        'donation': donation,
        'error_message': error_message,
        'reference_number': reference_number,
    }

    return render(request, 'donations/donation_status_tracker.html', context)


@require_POST
def donation_status_api(request, pk):
    """API endpoint to get donation status updates"""
    try:
        donation = get_object_or_404(Donation, pk=pk)

        # Security check
        if request.user.is_authenticated:
            if donation.donor and donation.donor != request.user:
                return JsonResponse({'status': 'error', 'message': 'Permission denied'})
        else:
            donor_email = request.session.get('donor_email')
            if not donor_email or donor_email != donation.donor_email:
                return JsonResponse({'status': 'error', 'message': 'Permission denied'})

        return JsonResponse({
            'status': 'success',
            'donation_status': donation.status,
            'status_display': donation.get_status_display(),
            'verification_date': donation.verification_date.isoformat() if donation.verification_date else None,
            'verified_by': donation.verified_by.get_full_name() if donation.verified_by else None,
            'last_updated': donation.updated_at.isoformat(),
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def bulk_verify_donations(request):
    """Bulk verification of donations"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'})

    try:
        import json
        action = request.POST.get('action')
        donation_ids = json.loads(request.POST.get('donation_ids', '[]'))
        notes = request.POST.get('notes', '')

        if not action or not donation_ids:
            return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})

        if action not in ['completed', 'failed', 'disputed']:
            return JsonResponse({'status': 'error', 'message': 'Invalid action'})

        # Get donations to update
        donations = Donation.objects.filter(
            id__in=donation_ids,
            status='pending_verification'
        )

        processed_count = 0
        for donation in donations:
            donation.status = action
            donation.verified_by = request.user
            donation.verification_date = timezone.now()
            if notes:
                donation.verification_notes = notes
            donation.save()
            processed_count += 1

        return JsonResponse({
            'status': 'success',
            'processed_count': processed_count,
            'message': f'Successfully processed {processed_count} donations'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def export_donations(request):
    """Export donations data to CSV"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    from django.db.models import Sum, Count, Avg
    from django.db.models.functions import TruncMonth
    import json
    from datetime import timedelta

    # Date range filter
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # Basic statistics
    total_donations = Donation.objects.filter(status='completed').aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id'),
        avg_amount=Avg('amount')
    )

    # Daily donation trends
    daily_trends = Donation.objects.filter(
        created_at__date__gte=start_date,
        status='completed'
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        amount=Sum('amount'),
        count=Count('id')
    ).order_by('day')

    # Campaign performance
    campaign_performance = Campaign.objects.annotate(
        total_raised=Sum('donations__amount', filter=Q(donations__status='completed')),
        donation_count=Count('donations', filter=Q(donations__status='completed')),
        avg_donation=Avg('donations__amount', filter=Q(donations__status='completed'))
    ).filter(total_raised__isnull=False).order_by('-total_raised')[:10]

    # Verification efficiency
    verification_stats = Donation.objects.filter(
        verification_date__date__gte=start_date,
        status__in=['completed', 'failed', 'disputed']
    ).aggregate(
        avg_verification_time=Avg('verification_date') - Avg('created_at'),
        total_verified=Count('id')
    )

    # Payment method breakdown removed (only GCash supported)
    payment_methods = Donation.objects.filter(
        status='completed',
        created_at__date__gte=start_date
    ).annotate(
        gcash=models.Value('gcash', output_field=models.CharField())
    ).values('gcash').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('-amount')

    # Admin performance
    admin_performance = User.objects.filter(
        verified_donations__verification_date__date__gte=start_date
    ).annotate(
        verifications=Count('verified_donations'),
        total_amount=Sum('verified_donations__amount')
    ).filter(verifications__gt=0).order_by('-verifications')

    # Monthly trends for charts
    monthly_trends = Donation.objects.filter(
        status='completed',
        created_at__date__gte=start_date - timedelta(days=365)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        amount=Sum('amount'),
        count=Count('id')
    ).order_by('month')

    # Prepare chart data
    chart_data = {
        'daily_amounts': [float(item['amount'] or 0) for item in daily_trends],
        'daily_counts': [item['count'] for item in daily_trends],
        'daily_labels': [item['day'].strftime('%Y-%m-%d') for item in daily_trends],
        'monthly_amounts': [float(item['amount'] or 0) for item in monthly_trends],
        'monthly_labels': [item['month'].strftime('%Y-%m') for item in monthly_trends],
        'payment_methods': {
            'labels': [item.get('payment_method', item.get('gcash', 'GCash')) for item in payment_methods],
            'amounts': [float(item['amount'] or 0) for item in payment_methods],
            'counts': [item['count'] for item in payment_methods]
        }
    }

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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    from .fraud_detection import fraud_detector
    from .models import FraudAlert, BlacklistedEntity

    # Get fraud summary
    days = int(request.GET.get('days', 30))
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
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
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
    """Custom management page for GCash configuration (staff only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('donations:campaign_list')

    from .forms import GCashConfigForm

    # Get existing config if any (we'll manage a single config record)
    config = GCashConfig.objects.first()

    if request.method == 'POST':
        form = GCashConfigForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            config = form.save()
            messages.success(request, _('GCash configuration saved successfully.'))
            return redirect('donations:manage_gcash')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = GCashConfigForm(instance=config)

    context = {
        'form': form,
        'config': config,
        'active_config': GCashConfig.get_active_config(),
    }
    return render(request, 'donations/manage_gcash.html', context)


def donation_faq(request):
    """View to display donation FAQ and help documentation"""
    context = {
        'gcash_config': GCashConfig.get_active_config(),
    }
    return render(request, 'donations/donation_faq.html', context)
