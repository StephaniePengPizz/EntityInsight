from django.urls import path
from knowledge_graph.views.construct_graph import load_data, export_graph
from knowledge_graph.views.show_graph_detail import find_relevant_nodes
from knowledge_graph.views.extract_relation import EntityExtractionView
from knowledge_graph.views.process_to_paragraph import ProcessArticlesView

urlpatterns = [
    path('load-data/', load_data, name='load_data'),
    path('export-graph/', export_graph, name='export_graph'),
    path('find-relevant-nodes/', find_relevant_nodes, name='find_relevant_nodes'),
    path('process-articles/', ProcessArticlesView.as_view(), name='process_articles'),
    path('extract-entities/', EntityExtractionView.as_view(), name='extract_entities'),
]