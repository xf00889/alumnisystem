"""Reusable, filter-preserving pagination for staff-only directory pages."""
from django import template

register = template.Library()


@register.inclusion_tag('admin/components/directory_pagination.html')
def admin_directory_pagination(page_obj, filters_query='', item_label='records'):
    """Show a condensed numbered page selector without losing active filters.

    page_obj is a Django Page. Query-string values are URL-encoded by the view,
    not assembled from arbitrary values in the HTML template.
    """
    if page_obj is None:
        return {'page_obj': None}
    paginator = page_obj.paginator
    return {
        'page_obj': page_obj,
        'page_numbers': paginator.get_elided_page_range(
            number=page_obj.number, on_each_side=1, on_ends=1
        ),
        'ellipsis': paginator.ELLIPSIS,
        'filters_query': filters_query or '',
        'item_label': item_label,
    }
