from django.shortcuts import render
import google.generativeai as genai
from EntityInsight import settings
from core.models import NewsArticle
import logging
logger = logging.getLogger(__name__)

def summarize_news(request):
    article_id = request.GET.get('id')
    article = NewsArticle.objects.get(id=article_id)
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(f"Summarize this article: {article.processed_content}")
    logger.info(response)
    return render(request, 'summary.html', {'summary': response.text})