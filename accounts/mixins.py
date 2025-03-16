from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class PaginationMixin:
    """
    A mixin that adds pagination functionality to any view.
    Usage:
    1. Add this mixin to your view
    2. Set items_per_page class variable (default is 10)
    3. In your get_context_data, call paginate_queryset(queryset)
    """
    items_per_page = 10

    def paginate_queryset(self, queryset, page_number=None):
        """
        Helper method to paginate any queryset
        """
        if page_number is None:
            page_number = self.request.GET.get('page', 1)
        
        paginator = Paginator(queryset, self.items_per_page)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        return page_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'get_queryset'):
            queryset = self.get_queryset()
            context['page_obj'] = self.paginate_queryset(queryset)
            context['object_list'] = context['page_obj'].object_list
        return context 