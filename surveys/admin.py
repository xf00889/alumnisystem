from django.contrib import admin
from .models import (
    Survey, SurveyQuestion, QuestionOption, SurveyResponse, ResponseAnswer,
    EmploymentRecord, Achievement, Report
)

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 3

class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 3
    show_change_link = True

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'start_date', 'end_date', 'created_by')
    list_filter = ('status', 'created_at', 'start_date', 'end_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    inlines = [SurveyQuestionInline]

@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'survey', 'question_type', 'is_required', 'display_order')
    list_filter = ('question_type', 'is_required', 'survey')
    search_fields = ('question_text', 'survey__title')
    inlines = [QuestionOptionInline]

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'alumni', 'submitted_at')
    list_filter = ('submitted_at', 'survey')
    search_fields = ('alumni__user__email', 'survey__title')
    date_hierarchy = 'submitted_at'

@admin.register(ResponseAnswer)
class ResponseAnswerAdmin(admin.ModelAdmin):
    list_display = ('response', 'question', 'get_answer')
    list_filter = ('question__question_type',)
    search_fields = ('question__question_text', 'text_answer')
    
    def get_answer(self, obj):
        if obj.selected_option:
            return obj.selected_option.option_text
        elif obj.text_answer:
            return obj.text_answer[:50]
        elif obj.rating_value:
            return f"Rating: {obj.rating_value}"
        return "No answer"
    get_answer.short_description = "Answer"

@admin.register(EmploymentRecord)
class EmploymentRecordAdmin(admin.ModelAdmin):
    list_display = ('alumni', 'job_title', 'company_name', 'industry', 'start_date', 'end_date')
    list_filter = ('industry', 'start_date')
    search_fields = ('alumni__user__email', 'company_name', 'job_title', 'industry')
    date_hierarchy = 'start_date'

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('alumni', 'title', 'achievement_type', 'achievement_date', 'verified')
    list_filter = ('achievement_type', 'achievement_date', 'verified')
    search_fields = ('alumni__user__email', 'title', 'description')
    date_hierarchy = 'achievement_date'

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'created_at', 'created_by', 'last_run')
    list_filter = ('report_type', 'created_at', 'last_run')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
