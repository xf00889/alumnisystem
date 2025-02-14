from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.sites import NotRegistered
from django.forms import ModelForm
from .models import Profile, Education, Experience, Skill, Document

User = get_user_model()

# Safely unregister the default User admin
try:
    admin.site.unregister(User)
except NotRegistered:
    pass

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username') if hasattr(User, 'username') else ('email',)

class ProfileAdminForm(ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'

class ProfileInline(admin.StackedInline):
    model = Profile
    form = ProfileAdminForm
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class EducationInline(admin.StackedInline):
    model = Education
    extra = 1

class ExperienceInline(admin.StackedInline):
    model = Experience
    extra = 1

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 3

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active') if hasattr(User, 'username') else ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name') if hasattr(User, 'username') else ('email', 'first_name', 'last_name')
    ordering = ('username',) if hasattr(User, 'username') else ('email',)
    inlines = (ProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('username', 'password') if hasattr(User, 'username') else ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email') if hasattr(User, 'username') else ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (('username', 'email') if hasattr(User, 'username') else ('email',)) + 
                     ('password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = ('user', 'phone_number', 'birth_date', 'country')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number')
    list_filter = ('is_public', 'created_at')
    inlines = [EducationInline, ExperienceInline, SkillInline, DocumentInline]
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'program', 'school', 'graduation_year')
    search_fields = ('profile__user__email', 'major', 'school')
    list_filter = ('program', 'school', 'graduation_year')

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'company', 'position', 'is_current')
    search_fields = ('profile__user__email', 'company', 'position')
    list_filter = ('is_current',)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('profile', 'name', 'skill_type', 'proficiency_level')
    search_fields = ('profile__user__email', 'name')
    list_filter = ('skill_type', 'proficiency_level')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'title', 'document_type', 'uploaded_at')
    search_fields = ('profile__user__email', 'title')
    list_filter = ('document_type', 'uploaded_at')
