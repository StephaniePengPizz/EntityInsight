import glob
import os
from datetime import datetime, timedelta

from django.shortcuts import redirect

from EntityInsight import settings
from core.constants import categories, entity_types, time_ranges
from core.models import NewsArticle, Entity, Relationship

from django.shortcuts import render

from core.views.summarize_news import summarize_for_category
from knowledge_graph.views.show_graph_detail import find_relevant_nodes, high_weight_paths_between_two_nodes
import concurrent
from concurrent.futures import ThreadPoolExecutor

def home(request):
    return render(request, 'home.html', {
        'categories': categories,
        'entity_types': entity_types,
        'time_ranges':time_ranges,
        'entity_count': ['one', 'two']
    })

from ahocorasick import Automaton
import time

def build_entity_automaton(entity_file_path):
    """Pre-process entity file into a fast Aho-Corasick automaton"""
    automaton = Automaton()
    with open(entity_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            entity = line.strip()
            if entity:  # skip empty lines
                automaton.add_word(entity, entity)
    automaton.make_automaton()
    return automaton

# Pre-process once (do this at startup)
entity_files = glob.glob(os.path.join(settings.MEDIA_ROOT, 'entity_extraction', 'pure_entities_*.txt'))
entity_files.sort(key=lambda x: os.path.basename(x).split('_')[1].split('.')[0], reverse=True)
file_path = entity_files[0]
entity_automaton = build_entity_automaton(file_path)

def extract_entities_fast(sentence):
    """Extract entities from sentence using pre-built automaton"""
    found_entities = set()
    for end_index, entity in entity_automaton.iter(sentence):
        found_entities.add(entity)
    return sorted(found_entities, key=len, reverse=True)


def results(request):
    if request.method == 'POST':
        sentence = request.POST.get('keywords', '')
        # Usage example:
        #sentence = "The Federal Reserve announced new regulations for Bank of America and JPMorgan Chase."

        keywords = extract_entities_fast(sentence)
        print('keywords', keywords)
        selected_categories = request.POST.getlist('categories', [])
        selected_entity_categories = request.POST.getlist('entity_types', [])
        selected_time_range = request.POST.get('time_ranges', '')
        selected_entity_count = request.POST.get('entity-count', 'one')  # 默认为一个实体
        print('selected_entity_count', selected_entity_count)
        # Filter by selected categories if any
        if selected_categories:
            articles = NewsArticle.objects.filter(category__in=selected_categories)
        else:
            articles = NewsArticle.objects.all()

        # Apply time range filter if selected
        if selected_time_range:
            time_range_map = {
                '1d': timedelta(days=1),
                '7d': timedelta(weeks=1),
                '14d': timedelta(weeks=2),
                '30d': timedelta(days=30),
                '90d': timedelta(days=90),
                '180d': timedelta(days=180),
                '365d': timedelta(days=365),
                '730d': timedelta(days=730),
                '1825d': timedelta(days=1825),
            }
            
            if selected_time_range in time_range_map:
                articles = articles.filter(
                    web_page__publication_time__gte=datetime.now() - time_range_map[selected_time_range]
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
        print("selected_categories", selected_categories)
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
        if selected_entity_count == 'one':
            result = find_relevant_nodes([entity_type], keywords[0]) if entity_type else None
            print("result", result)
            graph_description = generate_mermaid_graph(result) if result else None
        else:
            result = high_weight_paths_between_two_nodes(keywords[0], keywords[1], 5, 5)
            result2 = high_weight_paths_between_two_nodes(keywords[1], keywords[0], 5, 5)
            print("result", result)
            print("result2", result2)
            if result:
                graph_description = generate_mermaid_graph2(result)
            elif result2:
                graph_description = generate_mermaid_graph2(result)
            else:
                graph_description = None
            print("graph_description", graph_description)
        #print(llm_summaries)

        context = {
            'keywords': keywords,
            'selected_categories': selected_categories,
            'entity_category': selected_entity_categories[0] if selected_entity_categories else None,
            'news_by_category': news_by_category,
            'llm_summaries': llm_summaries,
            'result': result,
            'graph_description': graph_description,
            'time_range': selected_time_range,
            'entity_count': selected_entity_count
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


def generate_mermaid_graph2(paths_with_weights, top_n=5, show_weights=True, show_relations=True):
    """
    Generate a Mermaid graph using letters as node IDs and showing original labels.
    Format: A[Original Label] -->|relation| B[Next Label]
    """
    mermaid_code = "graph LR\n"

    # Get top N paths
    top_paths = paths_with_weights[:top_n]

    # Track nodes and assign letter IDs
    node_id_map = {}  # {original_node: letter_id}
    next_id = ord('A')
    edges = set()

    # First pass to assign letter IDs to all nodes
    for path, _, _, _ in top_paths:
        for node in path:
            if node not in node_id_map:
                node_id_map[node] = chr(next_id)
                next_id += 1

    # Generate edges
    for path, relations, _, weights in top_paths:
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]
            relation = relations[i]
            weight = weights[i]

            label_parts = []
            if show_relations:
                label_parts.append(relation)
            if show_weights:
                label_parts.append(f"w:{weight:.2f}")

            edge_label = "+".join(label_parts)
            edges.add((node_id_map[from_node], node_id_map[to_node], edge_label, from_node, to_node))

    # Add edges to graph
    for from_id, to_id, label, orig_from, orig_to in sorted(edges):
        mermaid_code += f"    {from_id}[{orig_from}] -->|{label}| {to_id}[{orig_to}]\n"

    return mermaid_code