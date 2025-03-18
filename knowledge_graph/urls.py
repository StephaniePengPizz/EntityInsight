from django.urls import path
from knowledge_graph.views.construct import load_data

urlpatterns = [
    path('load-data/', load_data, name='load_data'),
]