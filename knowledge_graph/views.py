from django.shortcuts import render
from core.models import NewsArticle, Entity, Relationship

def build_knowledge_graph(request):
    entity1 = Entity.objects.create(name="Company A", type="Company")
    entity2 = Entity.objects.create(name="Company B", type="Company")
    relationship = Relationship.objects.create(
        entity1=entity1,
        entity2=entity2,
        relationship_type="acquired",
        source_article=NewsArticle.objects.first(),
    )
    return render(request, 'graph_construction_success.html')