import csv
from django.views import View
from django.http import HttpResponse
from django.core.files.uploadedfile import InMemoryUploadedFile
from core.models import WebPage, NewsArticle
from datetime import datetime
from io import TextIOWrapper


class CSVDataImporterView(View):
    """Class-based view for importing data from CSV to WebPage and NewsArticle models"""

    def post(self, request):
        """Handle POST requests with CSV file upload"""
        try:
            if 'csv_file' not in request.FILES:
                return HttpResponse("No CSV file uploaded", status=400)

            csv_file = request.FILES['csv_file']
            results = self.process_csv(csv_file)

            return HttpResponse(
                f"Successfully imported {results['success']} records. "
                f"Failed: {results['failed']}. "
                f"Total processed: {results['total']}"
            )

        except Exception as e:
            return HttpResponse(f"Error occurred: {str(e)}", status=500)

    def process_csv(self, csv_file):
        """Process the uploaded CSV file"""
        if isinstance(csv_file, InMemoryUploadedFile):
            # Handle in-memory uploaded file
            csv_file = TextIOWrapper(csv_file.file, encoding='utf-8')

        reader = csv.DictReader(csv_file)
        results = {'success': 0, 'failed': 0, 'total': 0}

        for row in reader:
            results['total'] += 1
            try:
                self.process_row(row)
                results['success'] += 1
            except Exception as e:
                print(f"Failed to process row {row}: {str(e)}")
                results['failed'] += 1

        return results

    def process_row(self, row):
        """Process a single CSV row and save to database"""
        # Parse publication time (handle different formats)
        pub_time = self.parse_datetime(row.get('publication_time', ''))

        # Create or update WebPage
        web_page, created = WebPage.objects.update_or_create(
            url=row['url'],
            defaults={
                'title': row.get('title', ''),
                'source': row.get('source', 'csv_import'),
                'publication_time': pub_time,
                'credibility_score': float(row.get('credibility_score', 0.7)),
                'content': row.get('content', ''),
            }
        )

        # Create or update NewsArticle
        NewsArticle.objects.update_or_create(
            web_page=web_page,
            defaults={
                'category': row.get('category', 'general'),
                'keywords': row.get('keywords', ''),
                'processed_content': row.get('processed_content', ''),
            }
        )

    def parse_datetime(self, date_str):
        """Parse datetime from string with multiple format support"""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return None