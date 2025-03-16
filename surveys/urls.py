from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = 'surveys'

urlpatterns = [
    # Admin Survey Management URLs
    path('admin/surveys/', views.SurveyListView.as_view(), name='survey_list'),
    path('admin/surveys/create/', views.SurveyCreateView.as_view(), name='survey_create'),
    path('admin/surveys/<int:pk>/', views.SurveyDetailView.as_view(), name='survey_detail'),
    path('admin/surveys/<int:pk>/update/', views.SurveyUpdateView.as_view(), name='survey_update'),
    path('admin/surveys/<int:pk>/delete/', views.SurveyDeleteView.as_view(), name='survey_delete'),
    path('admin/surveys/<int:pk>/responses/', views.SurveyResponsesView.as_view(), name='survey_responses'),
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
    
    # Employment Record Management
    path('profile/employment/', views.EmploymentRecordListView.as_view(), name='employment_list'),
    path('profile/employment/add/', views.EmploymentRecordCreateView.as_view(), name='employment_create'),
    path('profile/employment/<int:pk>/update/', views.EmploymentRecordUpdateView.as_view(), name='employment_update'),
    
    # Achievement Management
    path('profile/achievements/', views.AchievementListView.as_view(), name='achievement_list'),
    path('profile/achievements/add/', views.AchievementCreateView.as_view(), name='achievement_create'),
    path('profile/achievements/<int:pk>/update/', views.AchievementUpdateView.as_view(), name='achievement_update'),
] 