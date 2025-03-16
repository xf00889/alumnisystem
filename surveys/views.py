from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, 
    FormView, TemplateView
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.forms import modelformset_factory
from django.db.models import Count, Avg, Q
from django.db import transaction
from django.utils import timezone
import json

from alumni_directory.models import Alumni
from .models import (
    Survey, SurveyQuestion, QuestionOption, SurveyResponse, 
    ResponseAnswer, EmploymentRecord, Achievement, Report
)
from .forms import (
    SurveyForm, SurveyQuestionForm, QuestionOptionForm, ResponseAnswerForm,
    EmploymentRecordForm, AchievementForm, ReportForm,
    SurveyQuestionFormSet, QuestionOptionFormSet
)

# Staff/Admin Views for Survey Management
@method_decorator(staff_member_required, name='dispatch')
class SurveyListView(ListView):
    model = Survey
    template_name = 'surveys/admin/survey_list.html'
    context_object_name = 'surveys'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get basic counts
        total_alumni = Alumni.objects.count()
        
        # Count unique alumni who have responded to any survey
        alumni_with_responses = Alumni.objects.filter(
            survey_responses__isnull=False
        ).distinct().count()
        
        # Calculate participation percentage
        participation_percentage = 0
        if total_alumni > 0:
            participation_percentage = round((alumni_with_responses / total_alumni) * 100, 1)
        
        # Count active surveys
        active_surveys = Survey.objects.filter(status='active').count()
        
        # Get response data by college
        college_data = SurveyResponse.objects.select_related('alumni').values(
            'alumni__college'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Format college data for the template
        formatted_college_data = []
        for item in college_data:
            if item['alumni__college']:
                formatted_college_data.append({
                    'college_name': item['alumni__college'],
                    'count': item['count']
                })
            
        # If no college data, add a default entry for testing/visualization
        if not formatted_college_data:
            # Add a sample entry if no real data exists
            formatted_college_data.append({
                'college_name': 'No College Data',
                'count': 1
            })
        
        # Get response data by graduation year (batch)
        batch_data = SurveyResponse.objects.values(
            'alumni__graduation_year'
        ).annotate(
            count=Count('id')
        ).order_by('alumni__graduation_year')
        
        # Get survey-specific response data
        survey_data = []
        for survey in self.get_queryset():
            responses_count = survey.responses.count()
            response_rate = 0
            if total_alumni > 0:
                response_rate = round((responses_count / total_alumni) * 100, 1)
            
            survey_data.append({
                'id': survey.id,
                'title': survey.title,
                'status': survey.status,
                'start_date': survey.start_date,
                'end_date': survey.end_date,
                'responses_count': responses_count,
                'response_rate': response_rate
            })
        
        # Add all data to context
        context.update({
            'total_alumni': total_alumni,
            'alumni_with_responses': alumni_with_responses,
            'participation_percentage': participation_percentage,
            'active_surveys': active_surveys,
            'college_data': formatted_college_data,
            'batch_data': batch_data,
            'survey_data': survey_data
        })
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/admin/survey_form.html'
    success_url = reverse_lazy('surveys:survey_list')

    def form_valid(self, form):
        # Set the created_by field to the current user
        form.instance.created_by = self.request.user
        
        # Get survey type and external URL
        is_external = self.request.POST.get('is_external') == 'true'
        form.instance.is_external = is_external
        
        # Save the survey first
        response = super().form_valid(form)
        
        if not is_external:
            # Process questions data
            try:
                questions_data = json.loads(self.request.POST.get('questions', '[]'))
                
                for question_data in questions_data:
                    # Create question
                    question = SurveyQuestion.objects.create(
                        survey=self.object,
                        question_text=question_data['question_text'],
                        question_type=question_data['question_type'],
                        is_required=question_data['is_required'],
                        help_text=question_data.get('help_text', ''),
                        display_order=question_data['display_order']
                    )
                    
                    # Add scale type if applicable
                    if question_data.get('scale_type'):
                        question.scale_type = question_data['scale_type']
                        question.save()
                    
                    # Create options if applicable
                    if 'options' in question_data:
                        for option_data in question_data['options']:
                            QuestionOption.objects.create(
                                question=question,
                                option_text=option_data['option_text'],
                                display_order=option_data['display_order']
                            )
            
            except json.JSONDecodeError:
                # Log the error but don't prevent survey creation
                print("Error processing questions data")
        
        # Return JSON response for AJAX submission
        return JsonResponse({
            'status': 'success',
            'redirect_url': self.get_success_url()
        })

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)

@method_decorator(staff_member_required, name='dispatch')
class SurveyUpdateView(UpdateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/admin/survey_form.html'
    success_url = reverse_lazy('surveys:survey_list')

@method_decorator(staff_member_required, name='dispatch')
class SurveyDeleteView(DeleteView):
    model = Survey
    template_name = 'surveys/admin/survey_confirm_delete.html'
    success_url = reverse_lazy('surveys:survey_list')

@method_decorator(staff_member_required, name='dispatch')
class SurveyDetailView(DetailView):
    model = Survey
    template_name = 'surveys/admin/survey_detail.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().prefetch_related('options')
        context['response_count'] = self.object.responses.count()
        return context

@method_decorator(staff_member_required, name='dispatch')
class SurveyResponsesView(DetailView):
    model = Survey
    template_name = 'surveys/admin/survey_responses.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = self.object
        
        # Get all responses for this survey with related alumni data
        responses = survey.responses.select_related('alumni__user').prefetch_related(
            'answers', 'answers__question', 'answers__selected_option'
        ).order_by('-submitted_at')
        
        # Process responses for easy display in template
        processed_responses = []
        for response in responses:
            response_data = {
                'id': response.id,
                'alumni_name': f"{response.alumni.user.first_name} {response.alumni.user.last_name}",
                'submitted_at': response.submitted_at,
                'answers': []
            }
            
            # Group answers by question
            for question in survey.questions.all():
                answer_objects = [a for a in response.answers.all() if a.question_id == question.id]
                
                # Skip if no answer exists for this question
                if not answer_objects:
                    continue
                
                answer_value = None
                # Handle different types of questions
                if question.question_type == 'text':
                    # Text answer
                    answer_value = answer_objects[0].text_answer if answer_objects else None
                    
                elif question.question_type == 'multiple_choice':
                    # Single selection
                    if answer_objects and answer_objects[0].selected_option:
                        answer_value = answer_objects[0].selected_option.option_text
                        
                elif question.question_type == 'checkbox':
                    # Multiple selections
                    if answer_objects:
                        options = [a.selected_option.option_text for a in answer_objects if a.selected_option]
                        answer_value = ", ".join(options) if options else None
                        
                elif question.question_type in ['rating', 'likert']:
                    # Rating value
                    answer_value = answer_objects[0].rating_value if answer_objects else None
                
                response_data['answers'].append({
                    'question': question.question_text,
                    'question_type': question.question_type,
                    'value': answer_value
                })
            
            processed_responses.append(response_data)
        
        # Calculate statistics for questions
        questions_stats = []
        for question in survey.questions.all():
            answers = ResponseAnswer.objects.filter(question=question)
            stat = {
                'question': question.question_text,
                'type': question.question_type,
                'total_answers': answers.count(),
            }
            
            if question.question_type in ['multiple_choice', 'checkbox']:
                # Calculate distribution of selected options
                stat['option_distribution'] = ResponseAnswer.objects.filter(
                    question=question
                ).values('selected_option__option_text').annotate(
                    count=Count('selected_option')
                ).exclude(selected_option__isnull=True)
                
            elif question.question_type in ['rating', 'likert']:
                # Calculate average rating
                avg_rating = answers.exclude(rating_value__isnull=True).aggregate(
                    avg=Avg('rating_value')
                )
                stat['rating_avg'] = round(avg_rating['avg'], 1) if avg_rating['avg'] else 0
                
                # Calculate distribution of ratings
                ratings = list(answers.exclude(rating_value__isnull=True).values_list('rating_value', flat=True))
                rating_distribution = {}
                for i in range(1, 6):  # Assuming 1-5 scale
                    rating_distribution[i] = len([r for r in ratings if r == i])
                stat['rating_distribution'] = rating_distribution
            
            questions_stats.append(stat)
        
        # Add to context
        context['responses'] = processed_responses
        context['questions_stats'] = questions_stats
        context['response_stats'] = {
            'total_responses': responses.count(),
            'response_rate': round((responses.count() / Alumni.objects.count()) * 100, 1) if Alumni.objects.count() > 0 else 0
        }
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class SurveyQuestionCreateView(CreateView):
    model = SurveyQuestion
    form_class = SurveyQuestionForm
    template_name = 'surveys/admin/question_form.html'
    
    def get_success_url(self):
        return reverse('surveys:survey_detail', kwargs={'pk': self.kwargs['survey_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        context['survey'] = survey
        
        if self.request.POST:
            context['option_formset'] = QuestionOptionFormSet(self.request.POST)
        else:
            context['option_formset'] = QuestionOptionFormSet()
            
        return context
    
    def form_valid(self, form):
        survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        form.instance.survey = survey
        
        context = self.get_context_data()
        option_formset = context['option_formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if form.instance.question_type in ['multiple_choice', 'checkbox'] and option_formset.is_valid():
                option_formset.instance = self.object
                option_formset.save()
                
        return HttpResponseRedirect(self.get_success_url())

@method_decorator(staff_member_required, name='dispatch')
class SurveyQuestionUpdateView(UpdateView):
    model = SurveyQuestion
    form_class = SurveyQuestionForm
    template_name = 'surveys/admin/question_form.html'
    
    def get_success_url(self):
        return reverse('surveys:survey_detail', kwargs={'pk': self.object.survey.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.object.survey
        
        if self.request.POST:
            context['option_formset'] = QuestionOptionFormSet(
                self.request.POST, 
                instance=self.object
            )
        else:
            context['option_formset'] = QuestionOptionFormSet(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        option_formset = context['option_formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if form.instance.question_type in ['multiple_choice', 'checkbox'] and option_formset.is_valid():
                option_formset.instance = self.object
                option_formset.save()
                
        return HttpResponseRedirect(self.get_success_url())

# Alumni-facing Views for Survey Responses
class SurveyTakeView(LoginRequiredMixin, DetailView):
    model = Survey
    template_name = 'surveys/take_survey.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questions = self.object.questions.all().prefetch_related('options')
        context['questions'] = questions
        
        # Check if already responded
        alumni = get_object_or_404(Alumni, user=self.request.user)
        context['already_responded'] = SurveyResponse.objects.filter(
            survey=self.object, 
            alumni=alumni
        ).exists()
        
        return context
    
    def post(self, request, *args, **kwargs):
        survey = self.get_object()
        alumni = get_object_or_404(Alumni, user=request.user)
        
        # Check if already responded
        if SurveyResponse.objects.filter(survey=survey, alumni=alumni).exists():
            messages.error(request, "You have already completed this survey.")
            return redirect('surveys:survey_list_public')
        
        # Create survey response
        response = SurveyResponse.objects.create(
            survey=survey,
            alumni=alumni,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Process answers for each question
        for question in survey.questions.all():
            answer_data = {}
            
            if question.question_type == 'text' or question.question_type == 'date':
                text_answer = request.POST.get(f'question_{question.id}')
                if text_answer:
                    answer_data['text_answer'] = text_answer
                    
            elif question.question_type == 'multiple_choice':
                option_id = request.POST.get(f'question_{question.id}')
                if option_id:
                    option = get_object_or_404(QuestionOption, id=option_id)
                    answer_data['selected_option'] = option
                    
            elif question.question_type == 'checkbox':
                # Handle multiple selections
                selected_options = []
                for option in question.options.all():
                    if request.POST.get(f'question_{question.id}_{option.id}'):
                        selected_options.append(option)
                
                # For checkbox, create multiple answers
                for option in selected_options:
                    ResponseAnswer.objects.create(
                        response=response,
                        question=question,
                        selected_option=option
                    )
                continue  # Skip the default creation below
                    
            elif question.question_type == 'rating':
                rating = request.POST.get(f'question_{question.id}')
                if rating:
                    answer_data['rating_value'] = int(rating)
            
            # Create the answer with collected data
            if answer_data or question.is_required:
                ResponseAnswer.objects.create(
                    response=response,
                    question=question,
                    **answer_data
                )
        
        messages.success(request, "Thank you for completing the survey!")
        return redirect('surveys:survey_list_public')

class SurveyListPublicView(LoginRequiredMixin, ListView):
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'
    
    def get_queryset(self):
        # Show all surveys with 'active' status, regardless of start/end dates
        # This ensures all active surveys are visible to alumni users
        return Survey.objects.filter(
            status='active'
        ).order_by('end_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mark surveys that user has already responded to
        alumni = get_object_or_404(Alumni, user=self.request.user)
        responded_surveys = SurveyResponse.objects.filter(
            alumni=alumni
        ).values_list('survey_id', flat=True)
        
        context['responded_surveys'] = responded_surveys
        return context

# Report generation views
@method_decorator(staff_member_required, name='dispatch')
class ReportListView(ListView):
    model = Report
    template_name = 'surveys/admin/report_list.html'
    context_object_name = 'reports'

@method_decorator(staff_member_required, name='dispatch')
class ReportCreateView(CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'surveys/admin/report_form.html'
    success_url = reverse_lazy('surveys:report_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Process dynamic filter fields into parameters JSON
        parameters = {}
        for field_name in self.request.POST:
            if field_name not in ['csrfmiddlewaretoken', 'title', 'description', 'report_type']:
                parameters[field_name] = self.request.POST[field_name]
        
        form.instance.parameters = parameters
        
        return super().form_valid(form)

@method_decorator(staff_member_required, name='dispatch')
class ReportDetailView(DetailView):
    model = Report
    template_name = 'surveys/admin/report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        
        # Generate report data based on type
        report_data = self.generate_report_data(report)
        context['report_data'] = report_data
        
        # Update last_run timestamp
        report.last_run = timezone.now()
        report.save(update_fields=['last_run'])
        
        return context
    
    def generate_report_data(self, report):
        """
        Generate report data based on report type and parameters
        """
        data = {
            'title': report.title,
            'type': report.report_type,
            'chart_data': {},
            'table_data': [],
            'summary': {}
        }
        
        if report.report_type == 'employment':
            # Employment trends report
            employment_records = EmploymentRecord.objects.all()
            
            # Apply filters from parameters
            if 'industry' in report.parameters and report.parameters['industry']:
                employment_records = employment_records.filter(
                    industry__icontains=report.parameters['industry']
                )
                
            if 'start_year' in report.parameters and report.parameters['start_year']:
                start_year = int(report.parameters['start_year'])
                employment_records = employment_records.filter(
                    start_date__year__gte=start_year
                )
                
            if 'end_year' in report.parameters and report.parameters['end_year']:
                end_year = int(report.parameters['end_year'])
                employment_records = employment_records.filter(
                    start_date__year__lte=end_year
                )
            
            # Industry distribution
            industry_counts = employment_records.values('industry').annotate(
                count=Count('id')
            ).order_by('-count')
            
            data['chart_data']['industries'] = {
                'labels': [item['industry'] for item in industry_counts],
                'data': [item['count'] for item in industry_counts],
            }
            
            # Job titles
            job_title_counts = employment_records.values('job_title').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            data['chart_data']['job_titles'] = {
                'labels': [item['job_title'] for item in job_title_counts],
                'data': [item['count'] for item in job_title_counts],
            }
            
            # Table data - recent employment records
            data['table_data'] = list(employment_records.values(
                'alumni__user__first_name', 'alumni__user__last_name',
                'company_name', 'job_title', 'industry', 'start_date'
            ).order_by('-start_date')[:50])
            
            # Summary statistics
            data['summary'] = {
                'total_records': employment_records.count(),
                'unique_companies': employment_records.values('company_name').distinct().count(),
                'unique_industries': employment_records.values('industry').distinct().count(),
            }
            
        elif report.report_type == 'geographic':
            # Geographic distribution report
            alumni_locations = Alumni.objects.select_related('location')
            
            # Apply filters
            if 'country' in report.parameters and report.parameters['country']:
                alumni_locations = alumni_locations.filter(
                    location__country__icontains=report.parameters['country']
                )
                
            if 'state' in report.parameters and report.parameters['state']:
                alumni_locations = alumni_locations.filter(
                    location__state__icontains=report.parameters['state']
                )
            
            # Country distribution
            country_counts = alumni_locations.values(
                'location__country'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            data['chart_data']['countries'] = {
                'labels': [item['location__country'] for item in country_counts if item['location__country']],
                'data': [item['count'] for item in country_counts if item['location__country']],
            }
            
            # State/province distribution (for top country)
            if country_counts and 'location__country' in country_counts[0]:
                top_country = country_counts[0]['location__country']
                state_counts = alumni_locations.filter(
                    location__country=top_country
                ).values(
                    'location__state'
                ).annotate(
                    count=Count('id')
                ).order_by('-count')
                
                data['chart_data']['states'] = {
                    'labels': [item['location__state'] for item in state_counts if item['location__state']],
                    'data': [item['count'] for item in state_counts if item['location__state']],
                    'country': top_country
                }
            
            # Table data - alumni locations
            data['table_data'] = list(alumni_locations.values(
                'user__first_name', 'user__last_name',
                'location__city', 'location__state', 'location__country'
            ).order_by('location__country', 'location__state')[:100])
            
            # Summary statistics
            data['summary'] = {
                'total_alumni': alumni_locations.count(),
                'countries_count': alumni_locations.values('location__country').distinct().count(),
                'cities_count': alumni_locations.values('location__city').distinct().count(),
            }
            
        elif report.report_type == 'achievements':
            # Alumni achievements report
            achievements = Achievement.objects.all()
            
            # Apply filters
            if 'achievement_type' in report.parameters and report.parameters['achievement_type']:
                achievements = achievements.filter(
                    achievement_type=report.parameters['achievement_type']
                )
                
            if 'start_date' in report.parameters and report.parameters['start_date']:
                achievements = achievements.filter(
                    achievement_date__gte=report.parameters['start_date']
                )
                
            if 'end_date' in report.parameters and report.parameters['end_date']:
                achievements = achievements.filter(
                    achievement_date__lte=report.parameters['end_date']
                )
            
            # Achievement types distribution
            type_counts = achievements.values('achievement_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            data['chart_data']['types'] = {
                'labels': [dict(Achievement.ACHIEVEMENT_TYPES).get(item['achievement_type'], item['achievement_type']) 
                          for item in type_counts],
                'data': [item['count'] for item in type_counts],
            }
            
            # Achievements by year
            year_counts = achievements.extra(
                select={'year': "EXTRACT(year FROM achievement_date)"}
            ).values('year').annotate(
                count=Count('id')
            ).order_by('year')
            
            data['chart_data']['years'] = {
                'labels': [int(item['year']) for item in year_counts],
                'data': [item['count'] for item in year_counts],
            }
            
            # Table data - recent achievements
            data['table_data'] = list(achievements.values(
                'alumni__user__first_name', 'alumni__user__last_name',
                'title', 'achievement_type', 'achievement_date', 'verified'
            ).order_by('-achievement_date')[:50])
            
            # Summary statistics
            data['summary'] = {
                'total_achievements': achievements.count(),
                'verified_count': achievements.filter(verified=True).count(),
                'top_type': dict(Achievement.ACHIEVEMENT_TYPES).get(
                    type_counts[0]['achievement_type']
                ) if type_counts else None,
            }
            
        elif report.report_type == 'feedback':
            # Survey feedback report
            surveys = Survey.objects.all()
            survey_responses = SurveyResponse.objects.all()
            
            # Get survey completion rate
            total_alumni = Alumni.objects.count()
            response_counts = survey_responses.values('survey').annotate(
                count=Count('alumni', distinct=True)
            )
            
            completion_rates = []
            for response in response_counts:
                survey = Survey.objects.get(id=response['survey'])
                completion_rates.append({
                    'survey': survey.title,
                    'responses': response['count'],
                    'rate': round((response['count'] / total_alumni) * 100, 1) if total_alumni > 0 else 0
                })
            
            data['chart_data']['completion'] = {
                'labels': [item['survey'] for item in completion_rates],
                'data': [item['rate'] for item in completion_rates],
            }
            
            # Get rating averages for rating questions
            rating_questions = SurveyQuestion.objects.filter(question_type='rating')
            rating_averages = []
            
            for question in rating_questions:
                avg_rating = ResponseAnswer.objects.filter(
                    question=question,
                    rating_value__isnull=False
                ).aggregate(avg=Avg('rating_value'))
                
                if avg_rating['avg']:
                    rating_averages.append({
                        'question': question.question_text,
                        'survey': question.survey.title,
                        'average': round(avg_rating['avg'], 2)
                    })
            
            data['chart_data']['ratings'] = {
                'labels': [f"{item['survey']}: {item['question'][:30]}..." for item in rating_averages],
                'data': [item['average'] for item in rating_averages],
            }
            
            # Table data - recent textual feedback
            text_answers = ResponseAnswer.objects.filter(
                text_answer__isnull=False
            ).exclude(
                text_answer=''
            ).select_related(
                'question', 'response__alumni', 'response__survey'
            ).order_by('-response__submitted_at')[:30]
            
            data['table_data'] = [
                {
                    'survey': answer.response.survey.title,
                    'question': answer.question.question_text,
                    'answer': answer.text_answer,
                    'alumni': f"{answer.response.alumni.user.first_name} {answer.response.alumni.user.last_name}",
                    'date': answer.response.submitted_at
                }
                for answer in text_answers
            ]
            
            # Summary statistics
            data['summary'] = {
                'total_surveys': surveys.count(),
                'total_responses': survey_responses.count(),
                'avg_completion_rate': round(
                    sum(item['rate'] for item in completion_rates) / len(completion_rates), 1
                ) if completion_rates else 0,
            }
            
        elif report.report_type == 'custom':
            # Placeholder for custom reports
            data['summary'] = {
                'message': 'Custom reports can be implemented based on specific needs'
            }
        
        return data

# Employment and Achievement record management for alumni
class EmploymentRecordCreateView(LoginRequiredMixin, CreateView):
    model = EmploymentRecord
    form_class = EmploymentRecordForm
    template_name = 'surveys/employment_form.html'
    success_url = reverse_lazy('surveys:employment_list')
    
    def form_valid(self, form):
        alumni = get_object_or_404(Alumni, user=self.request.user)
        form.instance.alumni = alumni
        return super().form_valid(form)

class EmploymentRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = EmploymentRecord
    form_class = EmploymentRecordForm
    template_name = 'surveys/employment_form.html'
    success_url = reverse_lazy('surveys:employment_list')
    
    def get_queryset(self):
        alumni = get_object_or_404(Alumni, user=self.request.user)
        return EmploymentRecord.objects.filter(alumni=alumni)

class EmploymentRecordListView(LoginRequiredMixin, ListView):
    model = EmploymentRecord
    template_name = 'surveys/employment_list.html'
    context_object_name = 'employment_records'
    
    def get_queryset(self):
        alumni = get_object_or_404(Alumni, user=self.request.user)
        return EmploymentRecord.objects.filter(alumni=alumni).order_by('-start_date')

class AchievementCreateView(LoginRequiredMixin, CreateView):
    model = Achievement
    form_class = AchievementForm
    template_name = 'surveys/achievement_form.html'
    success_url = reverse_lazy('surveys:achievement_list')
    
    def form_valid(self, form):
        alumni = get_object_or_404(Alumni, user=self.request.user)
        form.instance.alumni = alumni
        return super().form_valid(form)

class AchievementUpdateView(LoginRequiredMixin, UpdateView):
    model = Achievement
    form_class = AchievementForm
    template_name = 'surveys/achievement_form.html'
    success_url = reverse_lazy('surveys:achievement_list')
    
    def get_queryset(self):
        alumni = get_object_or_404(Alumni, user=self.request.user)
        return Achievement.objects.filter(alumni=alumni)

class AchievementListView(LoginRequiredMixin, ListView):
    model = Achievement
    template_name = 'surveys/achievement_list.html'
    context_object_name = 'achievements'
    
    def get_queryset(self):
        alumni = get_object_or_404(Alumni, user=self.request.user)
        return Achievement.objects.filter(alumni=alumni).order_by('-achievement_date')
