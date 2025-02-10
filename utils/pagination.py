from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """Custom pagination class with a default page size."""

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100
