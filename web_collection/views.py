# Create your views here.
from django.shortcuts import render
from core.models import WebPage

def collect_web_pages(request):
    new_page = WebPage.objects.create(
        url="https://example.com",
        title="Example Page",
        content="This is an example page.",
        source="Google",
        publication_time="2023-10-01T12:00:00Z",
        credibility_score=0.9,
    )
    return render(request, "collection_success.html")