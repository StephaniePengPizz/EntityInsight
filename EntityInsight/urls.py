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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('web-collection/', include('web_collection.urls')),
    path('text-classification/', include('text_classification.urls')),
    path('knowledge-graph/', include('knowledge_graph.urls')),
    path('genai-integration/', include('genai_integration.urls')),
    path('user-interface/', include('user_interface.urls')),  # Home page
]