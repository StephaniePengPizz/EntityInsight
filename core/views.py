from datetime import datetime, timedelta

from django.shortcuts import render, redirect

from core.constants import categories, entity_types, time_ranges
from core.models import NewsArticle, Entity, Relationship

from django.shortcuts import render

from genai_summarization.views import summarize_for_category
from knowledge_graph.views.show_graph_detail import find_relevant_nodes


def home(request):
    return render(request, 'home.html', {
        'categories': categories,
        'entity_types': entity_types,
        'time_ranges':time_ranges
    })

def results(request):
    if request.method == 'POST':
        keywords = request.POST.get('keywords', '')
        selected_categories = request.POST.getlist('categories', [])
        selected_entity_categories = request.POST.getlist('entity_types', [])
        selected_time_range = request.POST.getlist('time_ranges', [])

        # Get real news data from database
        news_by_category = {}

        # Filter by selected categories if any
        if selected_categories:
            articles = NewsArticle.objects.filter(category__in=selected_categories)
        else:
            articles = NewsArticle.objects.all()

        # Apply time range filter if selected
        if selected_time_range:
            time_ranges = {
                'last_24_hours': datetime.now() - timedelta(days=1),
                'last_week': datetime.now() - timedelta(weeks=1),
                'last_month': datetime.now() - timedelta(days=30),
            }

            for time_range in selected_time_range:
                if time_range in time_ranges:
                    articles = articles.filter(
                        web_page__publication_time__gte=time_ranges[time_range]
                    )

        # Organize articles by category
        for article in articles.select_related('web_page'):
            if article.category not in news_by_category:
                news_by_category[article.category] = []

            news_by_category[article.category].append({
                'title': article.web_page.title,
                'source': article.web_page.source,
                'date': article.web_page.publication_time.strftime('%Y-%m-%d'),
                'content': article.processed_content,
                'url': article.web_page.url,
            })

        # Generate summary for the first selected category
        summary_category = selected_categories if selected_categories else None
        print(summary_category)
        entity_type = selected_entity_categories[0] if selected_entity_categories else None
        result = find_relevant_nodes([entity_type], keywords)
        graph_description = generate_mermaid_graph(result)

        # Generate AI summary (you'll need to implement this function)
        llm_summaries = {}

        print(selected_categories)
        if selected_categories:
            # Summarize each selected category
            for category in selected_categories:
                category_news = news_by_category.get(category, [])
                if category_news:  # Only summarize if there are articles
                    llm_summaries[category] = summarize_for_category(
                        category,
                        category_news
                    )
        else:
            # If no categories selected, summarize all available categories
            for category, news_items in news_by_category.items():
                if news_items:  # Only summarize if there are articles
                    llm_summaries[category] = summarize_for_category(
                        category,
                        news_items
                    )

        # Generate a combined summary if needed
        combined_summary = None
        if llm_summaries:
            if len(llm_summaries) == 1:
                combined_summary = next(iter(llm_summaries.values()))
            else:
                # Combine multiple summaries into one (implement this function)
                combined_summary = combine_summaries(llm_summaries)


        context = {
            'keywords': keywords,
            'selected_categories': selected_categories,
            'entity_category': selected_entity_categories[0] if selected_entity_categories else None,
            'news_by_category': news_by_category,
            'llm_summaries': llm_summaries,  # Individual category summaries
            'combined_summary': combined_summary,  # Combined summary for display
            'result': result,
            'graph_description': graph_description,
        }

        return render(request, 'results.html', context)
    else:
        return redirect('home')


def generate_mermaid_graph(result):
    """
    Convert result['paths'] into a Mermaid diagram string using A[ActualName] format
    """
    node_map = {}  # Maps original node names to alphabetical labels
    current_char = ord('A')
    edges = set()

    # First pass: assign letters to all unique nodes
    for path_info in result['paths']:
        for node in path_info['nodes']:
            if node not in node_map:
                node_map[node] = chr(current_char)
                current_char += 1

    # Second pass: create edges with A[ActualName] format
    for path_info in result['paths']:
        path = path_info['nodes']
        relations = path_info['relations']
        for i in range(len(path) - 1):
            src = path[i]
            dst = path[i + 1]
            rel = relations[i]
            # Format: A[ActualName] -->|relation| B[ActualName]
            edge = f"{node_map[src]}[{src}] -->|{rel}| {node_map[dst]}[{dst}]"
            edges.add(edge)

    diagram = "graph LR\n" + "\n".join(edges)
    print(diagram)
    return diagram
