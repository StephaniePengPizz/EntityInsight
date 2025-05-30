import time

from django.views import View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
# from core.models import NewsArticle, WebPage
from bs4 import BeautifulSoup
import requests
import json
from dateutil.parser import parse
import re
from selenium import webdriver


class WebPageCollectorView(View):
    """Class-based view for collecting and processing web pages"""

    YAHOO_URL = 'https://finance.yahoo.com/news/'
    URLS = []
    driver = webdriver.Chrome()

    def get(self, request):
        """Handle GET requests to collect and process web pages"""
        #print(request.path)
        if request.path.find("rootpage") != -1:
            return self.get_URL(request)
        elif request.path.find("collect") != -1:
            return self.getpage(request)
        return HttpResponse(status=404)

    def get_URL(self, request=None):
        """
        From: Base URL
        To: sub URLs of this base URL, by updating self.URLS
        """
        try:
            # Step 1: Fetch and parse the main page

            # self.driver.get(self.YAHOO_URL)
            # time.sleep(3)  # Let dynamic content load
            # # return HttpResponse(f"Successfully collected data: Root (ID: RootID), content")
            #
            # # Step 2: Extract HTML and parse
            # html = self.driver.page_source
            # #return HttpResponse(html, content_type="text/plain", charset="utf-8")
            # response = HttpResponse(html, content_type="text/plain", charset="utf-8")
            # return response
            #html_content = ""
            with open('root.html', 'r', encoding='utf-8') as file:
                html_content = file.read()

            soup = BeautifulSoup(html_content, "html.parser")
            links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith(self.YAHOO_URL) and a['href'] != self.YAHOO_URL]
            links = list(set(links))
            return links






        except Exception as e:
            return HttpResponse(f"Error occurred: {str(e)}", status=500)

    def collect_pages(self):
        for url in self.URLS:
            self.getpage(url, '')

    def getpage(self, request):
        """COLLECT ONE SINGLE PAGE"""
        try:
            # Step 1: Fetch and parse the main page

            self.driver.get(self.YAHOO_URL)
            time.sleep(3)  # Let dynamic content load

            # Step 2: Extract HTML and parse
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            page_data = self.extract_structured_data_for_yahoo(soup)
            #print(page_data)
            # Step 3: Save to database
            web_page = self.save_to_database(page_data)

            return HttpResponse(f"Successfully collected data: {web_page.title} (ID: {web_page.id})")

        except Exception as e:
            return HttpResponse(f"Error occurred: {str(e)}", status=500)

    def extract_structured_data_for_yahoo(self, soup):
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

    def extract_structured_data_for_Reuter(self, soup):
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

    def save_to_database(self, page_data):
        """Save extracted data to database"""
        # Create or update WebPage
        web_page, created = WebPage.objects.update_or_create(
            url=self.YAHOO_URL,
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

    """
        def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver = self._init_selenium_driver()

    def _init_selenium_driver(self):

        options = Options()
        options.add_argument("--headless=new")  # Run in background
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=options)
        return driver
        
         #BASE_URL = 'https://www.reuters.com/business/finance/insurance-broker-hub-international-secures-29-billion-valuation-16-billion-2025-05-12/'
   
"""


def main():
    obj = WebPageCollectorView()  # 创建A类实例

    print(obj.get_URL())  # 调用b方法


if __name__ == "__main__":
    main()
