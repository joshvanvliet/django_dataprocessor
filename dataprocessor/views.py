from functools import reduce
from operator import or_

from django.core.paginator import Paginator
from django.db.models import Max, Q
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from .models import DataEntry

def dataentry_list(request: HttpRequest) -> HttpResponse:
    """Display paginated list of DataEntries with search functionality."""
    search_query = request.GET.get("q", "")
    queryset = DataEntry.objects.all().order_by("-dataString1")

    if search_query:
        search_fields = [
            "dataString0",  # URL
            "dataString1",  # Date/Time
            "dataString2",  # Category
            "dataString3",  # Postal Code
            "dataString4",  # Optional Field
            "dataString5",  # Numeric Value
            "unique_id",    # ID
        ]
        query_filters = [Q(**{f"{field}__icontains": search_query}) for field in search_fields]
        queryset = queryset.filter(reduce(or_, query_filters))

    paginator = Paginator(queryset, 20)
    page_number = request.GET.get("page")
    entries = paginator.get_page(page_number)

    context = {
        "entries": entries,
        "latest_date": DataEntry.objects.aggregate(Max("dataString1"))["dataString1__max"],
        "request": request,
    }
    
    return render(request, "dataentry_list.html", context)