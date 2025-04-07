# Create your views here.
import json
from datetime import datetime

from dateutil.parser import parse
from django.shortcuts import render
from core.models import NewsArticle, WebPage
from bs4 import BeautifulSoup
import re
import requests
import os
from django.conf import settings
from django.http import HttpResponse


def get_subdirectory_links(base_url):
    headers = {'User-Agent': 'Mozilla/5.0'}  # 设置请求头以模拟浏览器访问
    response = requests.get(base_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # 假设子目录链接在<a>标签内，且href属性以'/'开头（不包含域名）
        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('/')]
        # 过滤掉非子目录的链接（如图片、样式表等），这里简单假设子目录链接不以特定文件扩展名结尾
        subdirectory_links = [link for link in links if not link.endswith(('.html', '.jpg', '.css', '.js'))]
        return [base_url + link for link in subdirectory_links]  # 补全为完整URL
    else:
        print(f"请求失败，状态码: {response.status_code}")
        return []


def extract_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    # 过滤金融相关链接
    finance_links = [link for link in links if re.search(r'(finance|stock|bank)', link)]
    return finance_links


def extract_structured_data(soup):
    """从BeautifulSoup对象中提取结构化数据"""
    # 提取标题
    title = soup.title.string if soup.title else ""

    # 查找所有 script 标签，类型为 application/ld+json
    script_tag = soup.find('script', type='application/ld+json')
    json_data = json.loads(script_tag.string)

    # 提取时间信息
    date_published = json_data.get('datePublished')

    # 转换为 datetime 对象
    if date_published:
        date_published = parse(date_published)

    # 提取正文内容
    article_body = soup.find('article') or \
                   soup.find('div', class_=re.compile('article|content|main', re.I))
    content = article_body.get_text('\n', strip=True) if article_body else ""

    # 提取关键词
    keywords = []
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_meta:
        keywords = [k.strip() for k in keywords_meta.get('content', '').split(',') if k.strip()]

    return {
        'title': title,
        'publication_time': date_published,
        'keywords': ', '.join(keywords),
        'content': content
    }

def collect_web_pages(request):
    base_url = 'https://finance.yahoo.com/news/asia-credit-market-heats-issuers-040634997.html'
    subdirectory_urls = get_subdirectory_links(base_url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.yahoo.com/news'
    }
    i = 0
    # for url in subdirectory_urls:
    #     i = i + 1
    #     if i == 5:
    #         break
    #     response = requests.get(url, headers=headers)
    #     if response.status_code == 200:
    #         html_content = response.text
    #         soup = BeautifulSoup(html_content, 'html.parser')
    #         #title = soup.select_one('.article-title').text.strip()
    #         #print(title)
    #         #pub_time = soup.select_one('.publish-date').text.strip()
    #         new_page = WebPage.objects.create(
    #             url=url,
    #             title="",
    #             content=response.text,
    #             source="https://finance.yahoo.com/news/",
    #             publication_time="pub_time",
    #             credibility_score=0.9,
    #         )
    response = requests.get(base_url, headers=headers)

    soup = BeautifulSoup(response.text, 'html.parser')
    # 提取结构化数据
    page_data = extract_structured_data(soup)

    web_page, created = WebPage.objects.update_or_create(
        url=base_url,
        defaults={
            'title': page_data['title'],
            'source': 'yahoo finance',
            'publication_time': page_data['publication_time'],
            'credibility_score': 0.8,
        }
    )

    news_article = NewsArticle.objects.update_or_create(
        web_page=web_page,
        defaults={
            'category': 'default',
            'keywords': page_data['keywords'],
            'processed_content': page_data['content'],
        }
    )
    # 保存HTML到文件
    #with open(file_path, 'w', encoding='utf-8') as f:
    #    f.write(html_content)
    #try:
    #    with open(file_path, 'r', encoding='utf-8') as f:
    #        return HttpResponse(f.read())  # 直接返回HTML内容
    #except FileNotFoundError:
    #    return HttpResponse("内容未找到", status=404)


    return HttpResponse(f"成功保存结构化数据: {web_page.title} (ID: {web_page.id})")
