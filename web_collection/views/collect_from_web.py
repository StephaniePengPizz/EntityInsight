import time

from django.views import View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from core.models import NewsArticle, WebPage
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from dateutil.parser import parse
import re


class WebPageCollectorView(View):
    """Class-based view for collecting and processing web pages"""

    BASE_URL = 'https://www.reuters.com/business/finance/insurance-broker-hub-international-secures-29-billion-valuation-16-billion-2025-05-12/'
    YAHOO_URL = 'https://finance.yahoo.com/news/rich-dad-poor-dad-author-185506248.html'
    URLS = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver = self._init_selenium_driver()

    def _init_selenium_driver(self):
        """Configure Selenium to mimic a real browser."""
        options = Options()
        options.add_argument("--headless=new")  # Run in background
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=options)
        return driver

    def get_URL(self):
        """
        From: Base URL
        To: sub URLs of this base URL, by updating self.URLS
        """
        pass

    def collect_pages(self):
        for url in self.URLS:
            self.get(url, '')

    def get(self, request):
        """Handle GET requests to collect and process web pages"""
        try:
            # Step 1: Fetch and parse the main page

            self.driver.get(self.YAHOO_URL)
            time.sleep(3)  # Let dynamic content load

            # Step 2: Extract HTML and parse
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            page_data = self.extract_structured_data(soup)
            print(page_data)
            # Step 3: Save to database
            web_page = self.save_to_database(page_data)

            return HttpResponse(f"Successfully collected data: {web_page.title} (ID: {web_page.id})")

        except Exception as e:
            return HttpResponse(f"Error occurred: {str(e)}", status=500)

    def extract_structured_data(self, soup):
        """Extract structured data from BeautifulSoup object"""
        # Extract title
        title = soup.title.string if soup.title else ""

        # Extract JSON-LD data
        script_tag = soup.find('script', type='application/ld+json')
        json_data = json.loads(script_tag.string) if script_tag else {}

        # Parse publication date
        date_published = parse(json_data.get('datePublished')) if json_data.get('datePublished') else None

        # Extract article content
        article_body = (soup.find('article') or
                        soup.find('div', class_=re.compile('article|content|main', re.I)))
        content = article_body.get_text('\n', strip=True) if article_body else ""

        return {
            'title': title,
            'publication_time': date_published,
            'content': content
        }

    def extract_structured_data_for_R(self, soup):
        """Extract structured data from BeautifulSoup object"""
        # Extract title
        title = soup.title.string if soup.title else ""

        # Extract JSON-LD data
        script_tag = soup.find('script', type='application/ld+json')
        json_data = json.loads(script_tag.string) if script_tag else {}

        title = parse(json_data.get('title')) if json_data.get('title') else None

        # Parse publication date
        date_published = parse(json_data.get('published_time')) if json_data.get('published_time') else None

        # Extract article content
        article_body = (soup.find('article') or
                        soup.find('div', class_=re.compile('article|content|main', re.I)))
        content = article_body.get_text('\n', strip=True) if article_body else ""

        return {
            'title': title,
            'publication_time': date_published,
            'content': content
        }

    def extract_structured_data2(self, soup):
        title = soup.title.string.strip()
        paragraphs = soup.find_all('div', attrs={'data-testid': lambda x: x and x.startswith('paragraph-')})

        # 提取并组合成正文
        full_text = '\n'.join(p.get_text(strip=True) for p in paragraphs)
        return {
            'title': title,
            'paragraphs': full_text,
            'source_url': self.BASE_URL
        }


    def save_to_database(self, page_data):
        """Save extracted data to database"""
        # Create or update WebPage
        web_page, created = WebPage.objects.update_or_create(
            url=self.BASE_URL,
            defaults={
                'title': page_data['title'],
                'source': 'yahoo finance',
                'publication_time': page_data['publication_time'],
                'credibility_score': 0.8,
            }
        )

        # Create or update NewsArticle
        NewsArticle.objects.update_or_create(
            web_page=web_page,
            defaults={
                'category': 'default',
                'processed_content': page_data['content'],
            }
        )

        return web_page

    # Optional helper methods (uncomment if needed)
    # def get_subdirectory_links(self, base_url):
    #     """Get all subdirectory links from a base URL"""
    #     response = requests.get(base_url, headers=self.HEADERS)
    #     if response.status_code == 200:
    #         soup = BeautifulSoup(response.text, 'html.parser')
    #         links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('/')]
    #         return [base_url + link for link in links if not link.endswith(('.html', '.jpg', '.css', '.js'))]
    #     return []

    # def extract_links(self, html):
    #     """Extract finance-related links from HTML"""
    #     soup = BeautifulSoup(html, 'html.parser')
    #     links = [a['href'] for a in soup.find_all('a', href=True)]
    #     return [link for link in links if re.search(r'(finance|stock|bank)', link)]
