# Create your views here.
from django.shortcuts import render
from core.models import WebPage
from bs4 import BeautifulSoup
import re
import requests


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


def collect_web_pages(request):
    base_url = 'https://webb-site.com/'
    subdirectory_urls = get_subdirectory_links(base_url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://webb-site.com/'
    }
    i = 0
    for url in subdirectory_urls:
        i = i + 1
        if i == 5:
            break
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.select_one('.article-title').text.strip()
            print(title)
            pub_time = soup.select_one('.publish-date').text.strip()
            new_page = WebPage.objects.create(
                url=url,
                title="",
                content=response.text,
                source="https://webb-site.com/",
                publication_time="pub_time",
                credibility_score=0.9,
            )
    return render(request, 'collection_success.html')
