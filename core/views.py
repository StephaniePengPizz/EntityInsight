from django.shortcuts import render, redirect

from core.constants import categories, entity_types
from core.models import NewsArticle, Entity, Relationship

from django.shortcuts import render

from genai_summarization.views import summarize_for_category
from knowledge_graph.views.show_graph_detail import find_relevant_nodes


def home(request):
    return render(request, 'home.html', {
        'categories': categories,
        'entity_types': entity_types
    })

def results(request):
    if request.method == 'POST':
        keywords = request.POST.get('keywords', '')
        selected_categories = request.POST.getlist('categories', [])
        selected_entity_categories = request.POST.getlist('entity_types', [])
        summary_category = selected_categories[0] if selected_categories else None
        entity_type = selected_entity_categories[0] if selected_entity_categories else None

        # 生成特定类别的AI总结
        llm_summary = summarize_for_category(summary_category, keywords)

        result = find_relevant_nodes([entity_type], keywords)
        graph_description = generate_mermaid_graph(result)
        context = {
            'keywords': keywords,
            'summary_category': selected_categories[0],
            'entity_category': selected_entity_categories[0],
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