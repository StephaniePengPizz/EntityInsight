from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from core.models import WebPage, NewsArticle
import json


class ProcessArticlesView(View):
    def get(self, request):
        """处理外部HTTP GET请求"""
        result = self.get_processed_data(request)
        return JsonResponse(result)

    def get_processed_data(self, request=None):
        """可独立调用的核心方法"""
        articles = NewsArticle.objects.exclude(processed_content__isnull=True).exclude(processed_content__exact='')
        results = []

        for article in articles:
            paragraphs = self.split_paragraphs(article.processed_content)
            for i, para in enumerate(paragraphs, start=1):
                results.append({
                    'docid': article.id,
                    'paraid': i,
                    'content': para,
                })

        return {
            'status': 'success',
            'data': results,
            'count': len(results)
        }

    def split_paragraphs(self, text):
        """Split text into paragraphs based on newlines"""
        if not text:
            return []

        # Split by double newlines (common paragraph separation)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        # If no paragraphs found, try single newlines
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        return paragraphs