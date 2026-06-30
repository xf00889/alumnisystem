from django.urls import path
from django.views.generic.base import RedirectView
from . import views
from . import tracer_study

app_name = 'surveys'

urlpatterns = [
    # Dedicated Graduate Tracer Study (NOT routed through the generic survey
    # views or the public survey list).
    path('tracer-study/', tracer_study.tracer_study_alumni, name='tracer_study_alumni'),
    path('tracer-study/employer/', tracer_study.tracer_study_employer, name='tracer_study_employer'),
    path('tracer-study/reports/', tracer_study.tracer_study_reports, name='tracer_study_reports'),
    path('tracer-study/report/<int:survey_id>/', tracer_study.tracer_study_report, name='tracer_study_report'),
    path('tracer-study/response/<int:response_id>/filled-form/', tracer_study.tracer_study_filled_alumni_response_legacy, name='tracer_study_filled_alumni_response_legacy'),
    path('tracer-study/response/<str:response_token>/filled-form/', tracer_study.tracer_study_filled_alumni_response, name='tracer_study_filled_alumni_response'),
    path('tracer-study/report/<int:survey_id>/export/', tracer_study.tracer_study_report_export, name='tracer_study_report_export'),

    # Admin Survey Management URLs
    path('admin/surveys/', views.SurveyListView.as_view(), name='survey_list'),
    path('admin/surveys/create/', views.SurveyCreateView.as_view(), name='survey_create'),
    path('admin/surveys/<int:pk>/', views.SurveyDetailView.as_view(), name='survey_detail'),
    path('admin/surveys/<int:pk>/update/', views.SurveyUpdateView.as_view(), name='survey_update'),
    path('admin/surveys/<int:pk>/delete/', views.SurveyDeleteView.as_view(), name='survey_delete'),
    path('admin/surveys/<int:pk>/responses/', views.SurveyResponsesView.as_view(), name='survey_responses'),
    path('admin/surveys/<int:pk>/export/', views.survey_export_responses, name='survey_export_responses'),
    path('admin/surveys/<int:survey_id>/questions/add/', views.SurveyQuestionCreateView.as_view(), name='question_create'),
    path('admin/surveys/questions/<int:pk>/update/', views.SurveyQuestionUpdateView.as_view(), name='question_update'),
    path('admin/surveys/analytics/', RedirectView.as_view(pattern_name='surveys:survey_list', permanent=False), name='survey_analytics'),
    
    # Public Survey URLs
    path('', views.SurveyListPublicView.as_view(), name='survey_list_public'),
    path('<int:pk>/take/', views.SurveyTakeView.as_view(), name='survey_take'),
    
    # Report URLs
    path('admin/reports/', views.ReportListView.as_view(), name='report_list'),
    path('admin/reports/create/', views.ReportCreateView.as_view(), name='report_create'),
    path('admin/reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('admin/reports/<int:pk>/export-pdf/', views.report_export_pdf, name='report_export_pdf'),
    
    # Employment Record Management
    path('profile/employment/', views.EmploymentRecordListView.as_view(), name='employment_list'),
    path('profile/employment/add/', views.EmploymentRecordCreateView.as_view(), name='employment_create'),
    path('profile/employment/<int:pk>/update/', views.EmploymentRecordUpdateView.as_view(), name='employment_update'),
    
    # Achievement Management
    path('profile/achievements/', views.AchievementListView.as_view(), name='achievement_list'),
    path('profile/achievements/add/', views.AchievementCreateView.as_view(), name='achievement_create'),
    path('profile/achievements/<int:pk>/update/', views.AchievementUpdateView.as_view(), name='achievement_update'),
] 
