import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import networkx as nx
import csv
import io
import os
from EntityInsight import settings

# 全局变量，存储图和实体频率
G4 = nx.DiGraph()
entity_freq = {}
normalized_dict = {}
max_freq = 0

@csrf_exempt
def load_data(request):
    """加载数据并计算实体频率"""
    global G4, entity_freq, normalized_dict, max_freq

    file_path = os.path.join(settings.BASE_DIR, 'core/data', 'relations_test.json')
    # 读取关系数据
    with open(file_path, 'r', encoding='utf-8') as file:
        relations_all = json.load(file)

    # 计算实体频率
    for item in relations_all:
        rel = item['content']
        if rel[0] in entity_freq:
            entity_freq[rel[0]] += 1
        else:
            entity_freq[rel[0]] = 1
        if rel[2] in entity_freq:
            entity_freq[rel[2]] += 1
        else:
            entity_freq[rel[2]] = 1

    # 归一化实体频率
    def normalize_dict_values(input_dict):
        values = list(input_dict.values())
        min_val = min(values)
        max_val = max(values)
        return {key: (value - min_val) / (max_val - min_val) for key, value in input_dict.items()}

    normalized_dict = normalize_dict_values(entity_freq)

    # 构建图
    source_relation_freq = {}
    target_relation_freq = {}
    for item in relations_all:
        rel = item['content']
        if rel[0] not in source_relation_freq:
            source_relation_freq[rel[0]] = {}
        if rel[2] not in source_relation_freq[rel[0]]:
            source_relation_freq[rel[0]][rel[2]] = 1
        else:
            source_relation_freq[rel[0]][rel[2]] += 1

        if rel[2] not in target_relation_freq:
            target_relation_freq[rel[2]] = {}
        if rel[0] not in target_relation_freq[rel[2]]:
            target_relation_freq[rel[2]][rel[0]] = 1
        else:
            target_relation_freq[rel[2]][rel[0]] += 1

    for item in relations_all:
        rel = item['content']
        if rel[0] in source_relation_freq and rel[2] in source_relation_freq[rel[0]]:
            source_freq = source_relation_freq[rel[0]][rel[2]]
            target_freq = target_relation_freq[rel[2]][rel[0]]
            source_total_freq = sum(source_relation_freq[rel[0]].values())
            target_total_freq = sum(target_relation_freq[rel[2]].values())
            weight = (source_freq / source_total_freq) * (target_freq / target_total_freq) * (normalized_dict[rel[0]] + normalized_dict[rel[2]])
            G4.add_edge(rel[0], rel[2], relation=rel[1], weight=weight)

    return JsonResponse({'status': 'success', 'message': 'Data loaded and graph built'})

@csrf_exempt
def export_graph(request):
    """导出图为 CSV 文件"""
    global G4

    # 将图数据写入 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Node1', 'Node2', 'Relation', 'Weight'])

    for edge in G4.edges(data=True):
        writer.writerow([edge[0], edge[1], edge[2]['relation'], edge[2]['weight']])

    # 返回 CSV 文件
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=graph_data_2023_2024.csv'
    return response

@csrf_exempt
def get_top_edges(request):
    """获取权重最高的边"""
    global G4

    # 按权重排序边
    sorted_edges = sorted(G4.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)

    # 返回前 100 条边
    top_edges = []
    for edge in sorted_edges[:100]:
        top_edges.append({
            'source': edge[0],
            'target': edge[1],
            'relation': edge[2]['relation'],
            'weight': edge[2]['weight']
        })

    return JsonResponse({'status': 'success', 'top_edges': top_edges})