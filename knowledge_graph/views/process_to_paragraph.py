from datetime import datetime

from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views import View

from EntityInsight import settings
from core.models import WebPage, NewsArticle
import json
import os
import logging

logger = logging.getLogger(__name__)

class ProcessArticlesView(View):
    def get(self, request):
        """Handle external HTTP GET requests"""
        result = self.get_processed_data(request)

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"processed_articles_{timestamp}.json"
        self.save_to_json(result, filename)

        return JsonResponse(result)

    def get_processed_data(self, request=None):
        """Core method that can be called independently"""
        articles = NewsArticle.objects.exclude(
            processed_content__isnull=True
        ).exclude(
            processed_content__exact=''
        ).only('id', 'processed_content')  # Optimize query

        results = []

        for article in articles:
            paragraphs = self.split_paragraphs(article.processed_content)
            for i, para in enumerate(paragraphs, start=1):
                results.append({
                    'doc_id': f"{article.id}_{i}",  # More unique identifier
                    'article_id': article.id,
                    'para_id': i,
                    'content': para,
                })

        return {
            'status': 'success',
            'data': results,
            'count': len(results),
            'timestamp': timezone.now().isoformat()  # Add timestamp
        }

    def split_paragraphs(self, text):
        """Split text into paragraphs based on newlines"""
        if not text:
            return []

        # Normalize line endings and split
        paragraphs = [p.strip() for p in text.replace('\r\n', '\n').split('\n\n') if p.strip()]

        return paragraphs or [text.strip()]  # Return single paragraph if no splits

    def save_to_json(self, data, filename):
        """Save data to a JSON file in the media directory"""
        output_dir = os.path.join(settings.MEDIA_ROOT, 'processed_articles')
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, filename)

        try:

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save JSON file: {str(e)}")