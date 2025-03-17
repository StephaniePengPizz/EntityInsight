from django.shortcuts import render
from core.models import NewsArticle, Entity, Relationship

def home(request):
    """
    主页：显示分类新闻和知识图谱
    """
    categorized_news = NewsArticle.objects.all()
    entities = Entity.objects.all()
    relationships = Relationship.objects.all()
    return render(request, 'home.html', {
        'categorized_news': categorized_news,
        'entities': entities,
        'relationships': relationships,
    })