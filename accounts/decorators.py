from functools import wraps
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate(items_per_page=10):
    """
    Decorator to add pagination to function-based views.
    Usage:
    @paginate(items_per_page=10)
    def my_view(request):
        items = MyModel.objects.all()
        return render(request, 'template.html', {'items': items})
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            # Only process if it's a TemplateResponse
            if hasattr(response, 'context_data'):
                # Find the queryset in the context
                context = response.context_data
                for key, value in context.items():
                    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                        try:
                            # Try to paginate the queryset
                            paginator = Paginator(value, items_per_page)
                            page = request.GET.get('page', 1)
                            try:
                                page_obj = paginator.page(page)
                            except PageNotAnInteger:
                                page_obj = paginator.page(1)
                            except EmptyPage:
                                page_obj = paginator.page(paginator.num_pages)
                            
                            # Update the context
                            context[key] = page_obj.object_list
                            context['page_obj'] = page_obj
                            break
                        except (AttributeError, TypeError):
                            continue
            
            return response
        return _wrapped_view
    return decorator 