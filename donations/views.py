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

from .models import Campaign, CampaignType, Donation, DonorRecognition, CampaignUpdate
from .forms import DonationForm, CampaignFilterForm, CampaignForm

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
        form = DonationForm(
            request.POST,
            user=request.user,
            campaign=campaign
        )
        
        if form.is_valid():
            donation = form.save()
            
            # Set success message
            messages.success(
                request,
                _('Thank you for your donation! Your contribution has been recorded.')
            )
            
            # Redirect to donation confirmation page
            return redirect('donations:donation_confirmation', pk=donation.pk)
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
    payment_method = request.GET.get('payment_method')
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
    
    if payment_method:
        donations = donations.filter(payment_method=payment_method)
    
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
    payment_method_choices = Donation._meta.get_field('payment_method').choices
    
    context = {
        'donations': page_obj,
        'query_params': query_params,
        'filtered_total': filtered_total,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'all_campaigns': all_campaigns,
        'status_choices': status_choices,
        'payment_method_choices': payment_method_choices,
        'selected_campaign': int(campaign_id) if campaign_id and campaign_id.isdigit() else None,
        'selected_status': status,
        'selected_payment_method': payment_method,
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
    campaigns = Campaign.objects.all().select_related('campaign_type', 'created_by').order_by('-created')
    
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
    
    # Add campaign statistics
    for campaign in campaigns:
        # Get donation count
        campaign.donors_count = Donation.objects.filter(
            campaign=campaign,
            status='completed'
        ).values('donor').distinct().count()
        
        # Calculate current amount
        campaign.current_amount = Donation.objects.filter(
            campaign=campaign,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate progress percentage
        if campaign.goal_amount > 0:
            campaign.progress_percentage = int((campaign.current_amount / campaign.goal_amount) * 100)
        else:
            campaign.progress_percentage = 0
    
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
    
    # Generate payment method options
    payment_method_options = ""
    for method_code, method_name in Donation.PAYMENT_METHOD_CHOICES:
        selected = "selected" if method_code == donation.payment_method else ""
        payment_method_options += f'<option value="{method_code}" {selected}>{method_name}</option>'
    
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
            <div class="col-md-6">
                <label for="id_payment_method" class="form-label">Payment Method</label>
                <select name="payment_method" id="id_payment_method" class="form-select" required>
                    {payment_method_options}
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
        
        payment_method = request.POST.get('payment_method')
        if payment_method:
            donation.payment_method = payment_method
        
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
    
    context = {
        'form': form,
        'campaign': campaign,
    }
    
    return render(request, 'donations/campaign_form.html', context)
