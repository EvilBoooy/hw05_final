from django.core.paginator import Paginator

from .const import POSTLIM


def get_page_context(post_list, request):
    paginator = Paginator(post_list, POSTLIM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
