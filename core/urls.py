from django.urls import path
from core import views
from django.contrib import admin

urlpatterns = [
    path('', views.home_result.home, name='home'),
    path('results/', views.home_result.results, name='results'),
    path('admin_collect/', views.admin_collect.admin_web_collection, name='admin'),
]