from django.urls import path
from knowledge_graph.views.construct_graph import load_data, export_graph
from knowledge_graph.views.show_graph_detail import find_relevant_nodes

urlpatterns = [
    path('load-data/', load_data, name='load_data'),
    path('export-graph/', export_graph, name='export_graph'),
    path('find-relevant-nodes/', find_relevant_nodes, name='find_relevant_nodes'),
]