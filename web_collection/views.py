# Create your views here.
from django.shortcuts import render
from core.models import WebPage
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
    html_content = ''
    if response.status_code == 200:
        html_content = response.text
    print(settings.MEDIA_ROOT)
    print(1)
    save_dir = os.path.join(settings.MEDIA_ROOT, 'web_collection')
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, 'captured.html')

    # 保存HTML到文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())  # 直接返回HTML内容
    except FileNotFoundError:
        return HttpResponse("内容未找到", status=404)
    return render(request, 'collection_success.html')
