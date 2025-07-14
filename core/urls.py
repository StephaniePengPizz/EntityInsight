from django.urls import path, re_path
from django.views.generic.base import RedirectView
from django.http import HttpResponseRedirect
from urllib.parse import unquote
from core import views
import re


def extract_and_redirect(request, encoded_url):
    # Extract the actual URL from the malformed pattern
    match = re.search(r"<a href='(https?://[^']+)", encoded_url)
    if match:
        actual_url = match.group(1)
        print(actual_url)
        return HttpResponseRedirect(actual_url)
    return HttpResponseRedirect('/')  # Fallback redirect


urlpatterns = [
    path('', views.home_result.home, name='home'),
    path('results/', views.home_result.results, name='results'),
    path('admin_collect/', views.admin_collect.admin_web_collection, name='admin'),

    # Catch malformed URLs and redirect properly
    re_path(
        r'results/(?P<encoded_url>.+)$',
        extract_and_redirect,
        name='fix-malformed-url'
    ),
]