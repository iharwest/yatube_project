from django.core.paginator import Paginator

PAGE_SIZE: int = 10


def get_page_context(queryset, request):
    """Обработка паджинации страниц"""
    paginator = Paginator(queryset, PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }
