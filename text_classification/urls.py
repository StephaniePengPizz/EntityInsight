from django.urls import path
from . import views

urlpatterns = [
    path('classify/', views.classify_news, name='classify_news'),
]