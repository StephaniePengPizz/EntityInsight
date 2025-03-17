from django.shortcuts import render
import google.generativeai as genai
from django.conf import settings
from core.models import NewsArticle

def summarize_news(request):
    article_id = request.GET.get('id')
    article = NewsArticle.objects.get(id=article_id)
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(f"Summarize this article: {article.processed_content}")
    return render(request, 'summary.html', {'summary': response.text})