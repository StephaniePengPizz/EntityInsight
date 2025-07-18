import glob
import json
import os
import pickle
from tqdm import tqdm
import networkx as nx

from EntityInsight import settings
# Load graph data
graph_files = glob.glob(os.path.join(settings.MEDIA_ROOT, 'graph', 'graph_20250713.pkl'))
graph_files.sort(key=lambda x: os.path.basename(x).split('_')[1].split('.')[0], reverse=True)
file_path = graph_files[0]
with open(file_path, "rb") as file:
    graph = pickle.load(file)

# Load entity type data
entity_files = glob.glob(os.path.join(settings.MEDIA_ROOT, 'entity_extraction', 'entities_20250602.json'))
entity_files.sort(key=lambda x: os.path.basename(x).split('_')[1].split('.')[0], reverse=True)
file_path = entity_files[0]
with open(file_path, "r", encoding="utf-8") as file:
    json_file = json.load(file)
current_type_dict_word_list = json_file

def find_relevant_nodes(target_types, source):
    cutoff = 5
    num_paths = 5
    # Initialize result dictionary
    result = {
        "source": source,
        "target_types": target_types,
        "cutoff": cutoff,
        "paths": []
    }
    paths_with_weights = []
    for target_type in target_types:
        paths_with_weights = []
        print(target_type)
        entity_set = list(set(current_type_dict_word_list[target_type]))
        for node in entity_set:
            # Find all simple paths from source(use input) to every target node in the target types(user input)
            all_paths = nx.all_simple_paths(graph, source=source, target=node, cutoff=5)

            for path in all_paths:
                flag = True
                print(flag)
                weight_list = []
                docs_list = []
                relations_list = []

                for i in range(len(path) - 1):
                    edge_data = graph.get_edge_data(path[i], path[i + 1])
                    weight_list.append(edge_data['weight'] ** (1 / 3))
                    relations_list.append(edge_data['relation'])
                    docs_list.append(edge_data.get('docs', []))  # Get docs for this edge

                # Calculate the weight of each edge in the path
                total_weight = sum(weight_list)
                average_weight = total_weight / (len(path) - 1)

                # Check if all weights meet the threshold
                #for w in weight_list:
                #    if w < 0.05:
                #        flag = False

                # If all weights are valid, add the path to the list
                if flag:
                    paths_with_weights.append({
                        "path": path,
                        "relations": relations_list,
                        "weights": weight_list,
                        "average_weight": average_weight,
                        "docs": docs_list
                    })
                print(paths_with_weights)

        # Sort paths by their average weight in descending order
        paths_with_weights.sort(key=lambda x: x["average_weight"], reverse=True)

        for i, path_info in enumerate(paths_with_weights[:num_paths]):
            result["paths"].append({
                "rank": i + 1,
                "nodes": path_info["path"],
                "relations": path_info["relations"],
                "weights": path_info["weights"],
                "average_weight": path_info["average_weight"],
                "supporting_documents": path_info["docs"]
            })

    result['num_paths'] = min(num_paths, len(paths_with_weights))
    return result


def analyze_distribution(source, target, num_paths, cutoff):
    # 使用 all_simple_paths 函数找到所有简单路径
    all_paths = nx.all_simple_paths(graph, source=source, target=target, cutoff=cutoff)
    threshold_list = []
    for path in tqdm(all_paths):
        weight_list = [(graph.get_edge_data(path[i], path[i + 1])['weight']) ** (1 / 3) for i in range(len(path) - 1)]
        threshold_list.append(weight_list)
    my_list = []
    for item in threshold_list:
        for item2 in item:
            my_list.append(item2)

    sorted_lst = sorted(my_list)
    n = len(sorted_lst)
    if n % 2 == 0:
        median_value = (sorted_lst[n // 2 - 1] + sorted_lst[n // 2]) / 2
    else:
        median_value = sorted_lst[n // 2]
    print("Median:", median_value)
    return median_value


def high_weight_paths_between_two_nodes(source, target, num_paths, cutoff):
    #median_value = analyze_distribution(source, target, num_paths, cutoff)
    # 使用 all_simple_paths 函数找到所有简单路径
    all_paths = nx.all_simple_paths(graph, source=source, target=target, cutoff=cutoff)

    paths_with_weights = []
    for path in tqdm(all_paths):
        flag = True
        # 计算路径上所有边的权重之和
        weight_list = [(graph.get_edge_data(path[i], path[i + 1])['weight']) ** (1 / 3) for i in range(len(path) - 1)]
        total_weight = sum(weight_list)
        relations = [graph.get_edge_data(path[i], path[i + 1])['relation'] for i in range(len(path) - 1)]
        average_weight = total_weight / len(path)
        #for w in weight_list:
            #if w < median_value:
            #    flag = False
        #if flag == True:
        paths_with_weights.append((path, relations, average_weight, weight_list))

    # 根据路径权重进行排序
    paths_with_weights.sort(key=lambda x: x[2], reverse=True)

    # 输出权重较高的路径
    for i, (path, relations, weight, weight_list) in enumerate(paths_with_weights[:num_paths]):
        for j in range(len(path) - 1):
            temp = weight_list[j]
            print(f"{path[j]}-->[{relations[j]}{temp}]-->", end="")
        print(path[len(path) - 1], "平均权重", weight)
    return paths_with_weights
