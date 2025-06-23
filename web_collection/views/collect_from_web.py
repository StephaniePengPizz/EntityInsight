import time
import json
import re
from datetime import datetime

from django.views import View
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from bs4 import BeautifulSoup
from dateutil.parser import parse
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from core.models import NewsArticle, WebPage


class WebPageCollectorView(View):
    """Class-based view for collecting and processing web pages from financial news sources"""

    YAHOO_FINANCE_URL = 'https://finance.yahoo.com/news/'
    REUTERS_URL = 'https://www.reuters.com/'
    MAX_WAIT_TIME = 5  # seconds for Selenium to wait for page load
    driver = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_driver()

    def initialize_driver(self):
        """Initialize the Selenium WebDriver"""
        if not self.driver:
            try:
                self.driver = webdriver.Chrome()
                self.driver.implicitly_wait(self.MAX_WAIT_TIME)
            except WebDriverException as e:
                raise RuntimeError(f"Failed to initialize WebDriver: {str(e)}")

    def get(self, request):
        """Handle GET requests to collect and process web pages"""
        if "rootpage" in request.path:
            return self.collect_root_page()
        elif "collect" in request.path:
            return self.collect_news_pages()
        elif "fail" in request.path:
            return self.collext_fail_pages()
        return HttpResponseNotFound("Endpoint not found")

    def collect_root_page(self):
        """Collect and parse the root page to extract news article URLs"""
        try:
            # Fetch and parse the main page
            self.driver.get(self.YAHOO_FINANCE_URL)
            time.sleep(2)  # Allow dynamic content to load

            # Extract HTML and parse links
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Extract unique news article links
            links = {
                a['href'] for a in soup.find_all('a', href=True)
                if a['href'].startswith(self.YAHOO_FINANCE_URL)
                   and a['href'] != self.YAHOO_FINANCE_URL
            }

            return HttpResponse("\n".join(links), content_type="text/plain")

        except Exception as e:
            return HttpResponse(
                f"Error collecting root page: {str(e)}",
                status=500
            )

    def collect_fail_pages(self):
        try:
            fail_urls = []
            with open("fails.txt", "r") as file:
                content = file.read().strip()
                fail_urls = eval(content)
            results = []
            still_fail = []
            for url in fail_urls:  # Limit to 5 for demo purposes
                try:
                    article_data = self.process_news_page(url)
                    if article_data:
                        web_page = self.save_to_database(article_data)
                        results.append(f"Collected: {web_page.title}")
                except Exception as e:
                    still_fail.append(url)
                    results.append(f"Error processing {url}: {str(e)}")
            with open('fails.txt', "w") as file:
                file.write(str(still_fail))
            return HttpResponse("\n".join(results), content_type="text/plain")
        except Exception as e:
            return HttpResponse(
                f"Error in collection process: {str(e)}",
                status=500
            )

    def collect_news_pages(self, page_start=None, page_num=None):
        """Collect and process individual news pages"""
        try:
            # First get the article links from the root page
            root_response = self.collect_root_page()
            if root_response.status_code != 200:
                return root_response

            article_urls = root_response.content.decode().split("\n")
            chosen_urls = []
            if page_start is None:
                chosen_urls = article_urls
            else:
                chosen_urls = article_urls[page_start:page_start + page_num]

            # Process each article URL
            results = []
            with open("fails.txt", "r") as file:
                content = file.read().strip()
                fails = eval(content)
            for url in chosen_urls:  # Limit to 5 for demo purposes
                try:
                    article_data = self.process_news_page(url)
                    if article_data:
                        web_page = self.save_to_database(article_data)
                        results.append(f"Collected: {web_page.title}")
                except Exception as e:
                    fails.append(url)
                    results.append(f"Error processing {url}: {str(e)}")
            with open('fails.txt', "w") as file:
                file.write(str(fails))

            return HttpResponse("\n".join(results), content_type="text/plain")

        except Exception as e:
            return HttpResponse(
                f"Error in collection process: {str(e)}",
                status=500
            )

    def process_news_page(self, url):
        """Process a single news page and extract structured data"""
        try:
            self.driver.get(url)
            time.sleep(2)  # Allow dynamic content to load

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Determine which parser to use based on URL
            if url.startswith(self.YAHOO_FINANCE_URL):
                return self.extract_yahoo_data(soup, url)
            else:
                return None

        except Exception as e:
            raise RuntimeError(f"Failed to process page {url}: {str(e)}")

    def extract_yahoo_data(self, soup, url):
        """Extract structured data from Yahoo Finance articles"""
        # Extract JSON-LD data if available
        script_tag = soup.find('script', type='application/ld+json')
        json_data = json.loads(script_tag.string) if script_tag else {}

        # Extract title
        title = json_data.get('headline', '') or soup.title.string if soup.title else ""

        # Parse publication date
        date_published = None
        if json_data.get('datePublished'):
            try:
                date_published = parse(json_data['datePublished'])
            except (ValueError, TypeError):
                pass

        # Extract article content
        article_body = (soup.find('article') or
                        soup.find('div', class_=re.compile('article|content|main', re.I)))
        content = article_body.get_text('\n', strip=True) if article_body else ""

        return {
            'url': url,
            'title': title,
            'publication_time': date_published or datetime.now(),
            'content': content,
            'source': 'yahoo finance',
            'credibility_score': 0.8
        }

    def save_to_database(self, page_data):
        """Save extracted data to database"""
        # Create or update WebPage
        web_page, created = WebPage.objects.update_or_create(
            url=page_data['url'],
            defaults={
                'title': page_data['title'][:255],  # Ensure title fits in field
                'source': page_data['source'],
                'publication_time': page_data['publication_time'],
                'credibility_score': page_data['credibility_score'],
            }
        )

        # Create or update NewsArticle
        NewsArticle.objects.update_or_create(
            web_page=web_page,
            defaults={
                'category': self.determine_category(page_data),
                'processed_content': page_data['content'],
            }
        )

        return web_page

    def determine_category(self, page_data):
        """Determine article category based on content (simplified example)"""
        content = page_data['content'].lower()
        if any(word in content for word in ['stock', 'market', 'trading']):
            return 'markets'
        elif any(word in content for word in ['company', 'business', 'firm']):
            return 'business'
        elif any(word in content for word in ['tech', 'technology', 'digital']):
            return 'technology'
        return 'general'

    def __del__(self):
        """Clean up WebDriver when instance is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
