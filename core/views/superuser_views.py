from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import Http404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views import View
from core.forms.superuser_form import SuperuserCreationForm

User = get_user_model()

@method_decorator([csrf_protect, never_cache], name='dispatch')
class SuperuserCreationView(View):
    template_name = 'core/create_superuser.html'
    form_class = SuperuserCreationForm
    
    def dispatch(self, request, *args, **kwargs):
        # Check if a superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            # If superuser exists, make this page inaccessible
            raise Http404("Superuser creation is no longer available.")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            try:
                # Double-check that no superuser exists before creating
                if User.objects.filter(is_superuser=True).exists():
                    messages.error(request, 'A superuser already exists.')
                    raise Http404("Superuser creation is no longer available.")
                
                # Create the superuser
                user = form.save()
                
                messages.success(
                    request, 
                    f'Superuser "{user.username}" has been created successfully!'
                )
                
                # Redirect to homepage
                return redirect('/')
                
            except Exception as e:
                messages.error(
                    request, 
                    f'Error creating superuser: {str(e)}'
                )
        
        return render(request, self.template_name, {'form': form})