"""
URL configuration for EntityInsight project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include

from web_collection.views.collect_from_web import WebPageCollectorView

urlpatterns = [
    path('collect_yahoo/', WebPageCollectorView.as_view(), name='collect-webpages-yahoo'),
    path('rootpage_yahoo/', WebPageCollectorView.as_view(), name='root-page-yahoo'),
    path('keep_yahoo/', WebPageCollectorView.as_view(), name='keep-collecting-yahoo'),
    path('collect_reuters/', WebPageCollectorView.as_view(), name='collect-webpages-reuters'),
    path('rootpage_reuters/', WebPageCollectorView.as_view(), name='root-page-reuters'),
    path('keep_reuters/', WebPageCollectorView.as_view(), name='keep-collecting-reuters'),
    path('collect_eastmoney/', WebPageCollectorView.as_view(), name='collect-webpages-eastmoney'),
    path('rootpage_eastmoney/', WebPageCollectorView.as_view(), name='root-page-eastmoney'),
    path('keep_eastmoney/', WebPageCollectorView.as_view(), name='keep-collecting-eastmoney'),
    path('fail/', WebPageCollectorView.as_view(), name='fail-page'),
]