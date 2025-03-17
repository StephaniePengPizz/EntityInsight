from django.urls import path
from . import views

urlpatterns = [
    path('build/', views.build_knowledge_graph, name='build_knowledge_graph'),
]