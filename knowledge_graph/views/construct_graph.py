import copy
import json
import pickle
from datetime import datetime

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import networkx as nx
import csv
import io
import os
from EntityInsight import settings
from core.models import Entity, Relationship, NewsArticle
from knowledge_graph.tool import normalize_dict_values, state_top3, state_string_trans

@csrf_exempt
def load_relations_and_construct_graph(request):
    timestamp = datetime.now().strftime("%Y%m%d")
    relations_path = os.path.join(settings.MEDIA_ROOT, 'relation_extraction', f'relations_{timestamp}.json')

    with open(relations_path, 'r', encoding='utf-8') as file:
        file_all = json.load(file)

    data = file_all['data']
    relations_all = []
    # 新增：三元组及其文档来源映射，key=(source, relation, target), value=[{'doc_id','url'}, ...]
    edge_docs = dict()

    for doc in data:
        doc_id = doc.get('doc_id')  # 你实际json每个doc的id字段，若不是请替换此行的键
        for rel in doc['relations']:
            # 如果关系本身不带doc_id，则用外层doc的doc_id；如果带（如rel[3]），可用rel[3]
            rel_doc_id = doc_id    # 若确认 rel[3] 存在，可以用 rel[3] 替换这里
            source, relation, target = rel[0], rel[1], rel[2]
            # 聚合所有同一个 (source, relation, target) 的文档信息
            key = (source, relation, target)
            url = ""
            if rel_doc_id:
                base_id = rel_doc_id.split('_')[0]
                try:
                    article = NewsArticle.objects.get(id=base_id)
                    url = article.web_page.url
                except NewsArticle.DoesNotExist:
                    url = ""

            if key not in edge_docs:
                edge_docs[key] = []
            edge_docs[key].append({
                'doc_id': rel_doc_id,
                'url': url
            })
            relations_all.append(rel)

    # Calculate entity frequencies
    entity_freq = {}
    for rel in relations_all:
        entity_freq[rel[0]] = entity_freq.get(rel[0], 0) + 1
        entity_freq[rel[2]] = entity_freq.get(rel[2], 0) + 1

    normalized_entity_freq = normalize_dict_values(entity_freq)

    # Store entity objects in database
    for entity_name, freq in entity_freq.items():
        Entity.objects.update_or_create(name=entity_name, defaults={'frequency': freq})

    # Before storing relation objects in database, calculate weight first
    source_relation_freq = {}
    target_relation_freq = {}
    for rel in relations_all:
        source = rel[0]
        target = rel[2]

        # weight part 1
        if source not in source_relation_freq:
            source_relation_freq[source] = {}
        source_relation_freq[source][target] = source_relation_freq[source].get(target, 0) + 1

        # weight part 2
        if target not in target_relation_freq:
            target_relation_freq[target] = {}
        target_relation_freq[target][source] = target_relation_freq[target].get(source, 0) + 1

    # Store relation objects in database
    g = nx.DiGraph()
    for rel in relations_all:
        source = rel[0]
        target = rel[2]

        source_freq = source_relation_freq[source].get(target, 0)
        target_freq = target_relation_freq[target].get(source, 0)
        source_total_freq = sum(source_relation_freq[source].values())
        target_total_freq = sum(target_relation_freq[target].values())

        weight = (source_freq / source_total_freq) * (target_freq / target_total_freq) * (normalized_entity_freq[source] + normalized_entity_freq[target])

        edge_data = g.get_edge_data(rel[0], rel[2])

        if edge_data is not None:
            g.remove_edge(rel[0], rel[2])
            relations_str = state_string_trans(edge_data['relation'], rel[1])

        else:
            if rel[1] == '':
                continue
            relations_str = rel[1] + '1'

        # 关键：把文档信息 docs 聚合到每条边属性上，按 (source, relation, target) 取
        key = (rel[0], rel[1], rel[2])
        g.add_edge(rel[0], rel[2], relation=relations_str, weight=weight, docs=edge_docs.get(key, []))

    g2 = copy.deepcopy(g)
    for source, target, edge in g.edges(data=True):
        try:
            new_relations_str = state_top3(edge['relation'])
        except:
            print(source, target, edge['relation'])
        weight = edge['weight']

        # get entity object
        source_entity = Entity.objects.get(name=source)
        target_entity = Entity.objects.get(name=target)

        # 此处务必保留 docs 属性（沿用 g 的边属性）
        docs = edge.get("docs", [])
        g2.remove_edge(source, target)
        g2.add_edge(source, target, relation=new_relations_str, weight=weight, docs=docs)

        Relationship.objects.update_or_create(
            source=source_entity,
            target=target_entity,
            defaults={
                'relation_type': new_relations_str,
                'weight': weight
            }
        )

    timestamp = datetime.now().strftime("%Y%m%d")
    file_path = os.path.join(settings.MEDIA_ROOT, 'graph', f'graph_{timestamp}.pkl')
    with open(file_path, "wb") as f:
        pickle.dump(g2, f)

    return JsonResponse({'status': 'success', 'message': 'Data loaded and stored in database and pickle file'})

@csrf_exempt
def export_graph(request):
    # fetch relationships from database
    relations = Relationship.objects.select_related('source', 'target').all()

    # create csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Node1', 'Node2', 'Relation', 'Weight'])

    for relation in relations:
        writer.writerow([relation.source.name, relation.target.name, relation.relation_type, relation.weight])

    # return csv
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=graph_data_2023_2024.csv'
    return response