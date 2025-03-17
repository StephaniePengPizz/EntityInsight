from django.shortcuts import render
from core.models import NewsArticle, WebPage

def classify_news(request):
    article = NewsArticle.objects.create(
        web_page=WebPage.objects.first(),
        category="Finance",
        processed_content="Processed content here...",
    )
    return render(request, 'classification_success.html')