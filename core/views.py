from django.shortcuts import render, redirect
from core.models import NewsArticle, Entity, Relationship

from django.shortcuts import render

from genai_integration.views import summarize_for_category
from knowledge_graph.views.show_graph_detail import find_relevant_nodes


def home(request):
    categories = [
        {'name': 'Finance', 'slug': 'finance'},
        {'name': 'Company', 'slug': 'company'},
        {'name': 'Macro', 'slug': 'macro'},
        {'name': 'Politics', 'slug': 'politics'},
        {'name': 'Technology', 'slug': 'technology'},
        {'name': 'Real Estate', 'slug': 'realestate'},
        {'name': 'Automotive', 'slug': 'automotive'},
        {'name': 'Consumer', 'slug': 'consumer'},
        {'name': 'Energy', 'slug': 'energy'},
        {'name': 'Health', 'slug': 'health'},
        {'name': 'Environment', 'slug': 'environment'},
        {'name': 'Livelihoods', 'slug': 'livelihoods'},
    ]
    return render(request, 'home.html', {'categories': categories})


def results(request):
    if request.method == 'POST':
        keywords = request.POST.get('keywords', '')
        selected_categories = request.POST.getlist('categories', [])

        # sample data
        news_by_category = {
            'Regulatory Actions': [
                {'title': 'SEC fines Bank of America $25M for reporting violations',
                 'source': 'Financial Times', 'date': '2023-11-15'},
                {'title': 'New banking capital requirements announced',
                 'source': 'Reuters', 'date': '2023-11-12'},
            ],
            'Financial Reports': [
                {'title': 'BOA Q3 earnings beat estimates despite penalty',
                 'source': 'Bloomberg', 'date': '2023-11-08'},
            ],
            'Market Impact': [
                {'title': 'Bank stocks dip after new regulations announcement',
                 'source': 'Wall Street Journal', 'date': '2023-11-10'},
            ],
            'Sample': [
                {'title': 'Bank stocks dip after new regulations announcement',
                 'source': 'Wall Street Journal', 'date': '2023-11-10'},
            ]
        }
        summary_category = selected_categories[0] if selected_categories else None

        # 生成特定类别的AI总结
        llm_summary = summarize_for_category(summary_category, news_by_category.get(summary_category, 'Finance'))
        #llm_summary = "summary placeholder"

        result = find_relevant_nodes(request)
        graph_description = generate_mermaid_graph(result)
        context = {
            'keywords': keywords,
            'summary_category': selected_categories[0],
            'news_by_category': news_by_category,
            'result': result,
            'graph_description': graph_description,
            'llm_summary': llm_summary,
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