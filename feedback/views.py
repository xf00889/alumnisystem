from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Feedback
from .forms import FeedbackForm, FeedbackAdminForm
from core.models import UserEngagement
from core.decorators import staff_or_coordinator_required

@login_required
def submit_feedback(request):
    """View for users to submit feedback"""
    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            
            # Track user engagement for feedback submission
            UserEngagement.objects.create(
                user=request.user,
                activity_type='feedback',
                points=5,  # Assign points for feedback submission
                description=f"Submitted feedback: {feedback.subject}"
            )
            
            messages.success(request, 'Thank you for your feedback! We will review it shortly.')
            return redirect('feedback:my_feedbacks')
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback/submit_feedback.html', {'form': form})

@login_required
def my_feedbacks(request):
    """View for users to see their submitted feedbacks"""
    feedbacks = Feedback.objects.filter(user=request.user)
    paginator = Paginator(feedbacks, 10)
    page = request.GET.get('page')
    feedbacks = paginator.get_page(page)
    
    return render(request, 'feedback/my_feedbacks.html', {'feedbacks': feedbacks})

@login_required
def feedback_detail(request, pk):
    """View for users to see their feedback details"""
    feedback = get_object_or_404(Feedback, pk=pk, user=request.user)
    return render(request, 'feedback/feedback_detail.html', {'feedback': feedback})

@staff_or_coordinator_required
def manage_feedbacks(request):
    """Admin view to manage all feedbacks"""
    # Get filter parameters
    status = request.GET.get('status')
    category = request.GET.get('category')
    priority = request.GET.get('priority')
    search = request.GET.get('search')
    
    # Start with all feedbacks
    feedbacks = Feedback.objects.all()
    
    # Apply filters
    if status:
        feedbacks = feedbacks.filter(status=status)
    if category:
        feedbacks = feedbacks.filter(category=category)
    if priority:
        feedbacks = feedbacks.filter(priority=priority)
    if search:
        feedbacks = feedbacks.filter(
            Q(subject__icontains=search) |
            Q(message__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(feedbacks, 20)
    page = request.GET.get('page')
    feedbacks = paginator.get_page(page)
    
    context = {
        'feedbacks': feedbacks,
        'status_choices': Feedback.STATUS_CHOICES,
        'category_choices': Feedback.CATEGORY_CHOICES,
        'priority_choices': Feedback.PRIORITY_CHOICES,
        'current_filters': {
            'status': status,
            'category': category,
            'priority': priority,
            'search': search
        }
    }
    
    return render(request, 'feedback/manage_feedbacks.html', context)

@staff_or_coordinator_required
def update_feedback(request, pk):
    """Admin view to update feedback status and add notes"""
    feedback = get_object_or_404(Feedback, pk=pk)
    
    if request.method == 'POST':
        form = FeedbackAdminForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            messages.success(request, 'Feedback updated successfully.')
            return redirect('feedback:manage_feedbacks')
    else:
        form = FeedbackAdminForm(instance=feedback)
    
    return render(request, 'feedback/update_feedback.html', {
        'form': form,
        'feedback': feedback
    })
