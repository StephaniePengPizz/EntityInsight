from datetime import datetime, timedelta

from django.shortcuts import redirect

from core.constants import categories, entity_types, time_ranges
from core.models import NewsArticle, Entity, Relationship

from django.shortcuts import render

from core.views.summarize_news import summarize_for_category
from knowledge_graph.views.show_graph_detail import find_relevant_nodes
import concurrent
from concurrent.futures import ThreadPoolExecutor

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
        selected_time_range = request.POST.get('time_ranges', '')

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

            if selected_time_range in time_ranges:
                articles = articles.filter(
                    web_page__publication_time__gte=time_ranges[selected_time_range]
                )

        # Organize articles by category
        recent_articles = articles.select_related('web_page').order_by('-created_at')
        news_by_category = {}

        for article in recent_articles:
            if article.category not in news_by_category:
                news_by_category[article.category] = []

            # Only append if the category has fewer than 10 articles
            if len(news_by_category[article.category]) < 10:
                news_by_category[article.category].append({
                    'title': article.web_page.title,
                    'source': article.web_page.source,
                    'date': article.web_page.publication_time.strftime('%Y-%m-%d'),
                    'content': article.processed_content,
                    'url': article.web_page.url,
                })

        llm_summaries = {}
        print(selected_categories)
        def generate_single_summary(category, keywords, news_items):
            if news_items:
                return summarize_for_category(category, keywords, news_items)
            return None

        # Use ThreadPoolExecutor to generate summaries in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            # If specific categories selected
            if selected_categories:
                future_to_category = {
                    executor.submit(
                        generate_single_summary,
                        category,
                        keywords,
                        news_by_category.get(category, [])
                    ): category
                    for category in selected_categories
                }
            else:
                # If no categories selected, summarize all available
                future_to_category = {
                    executor.submit(
                        generate_single_summary,
                        category,
                        keywords,
                        news_items
                    ): category
                    for category, news_items in news_by_category.items()
                }

            for future in concurrent.futures.as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    summary = future.result()
                    if summary:
                        llm_summaries[category] = summary
                except Exception as e:
                    print(f"Error generating summary for {category}: {str(e)}")
                    llm_summaries[category] = f"Summary generation failed for {category}"

        # Generate entity graph
        entity_type = selected_entity_categories[0] if selected_entity_categories else None
        result = find_relevant_nodes([entity_type], keywords) if entity_type else None
        graph_description = generate_mermaid_graph(result) if result else None
        print(llm_summaries)

        context = {
            'keywords': keywords,
            'selected_categories': selected_categories,
            'entity_category': selected_entity_categories[0] if selected_entity_categories else None,
            'news_by_category': news_by_category,
            'llm_summaries': llm_summaries,
            'result': result,
            'graph_description': graph_description,
            'time_range': selected_time_range,
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
