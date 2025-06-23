import glob
import json
import os
import pickle
from datetime import datetime

import networkx as nx
from django.shortcuts import render

from EntityInsight import settings


def find_relevant_nodes(target_types, source):
    cutoff = 5
    num_paths = 5

    # Load graph data
    graph_files = glob.glob(os.path.join(settings.MEDIA_ROOT, 'graph', 'graph_20250602.pkl'))
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
    # Initialize result dictionary
    result = {
        "source": source,
        "target_types": target_types,
        "cutoff": cutoff,
        "paths": []
    }
    print(current_type_dict_word_list)
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
                weight_list = [(graph.get_edge_data(path[i], path[i + 1])['weight']) ** (1 / 3) for i in
                               range(len(path) - 1)]

                # Calculate the weight of each edge in the path
                total_weight = sum(weight_list)

                # Extract relations between nodes in the path
                relations = [graph.get_edge_data(path[i], path[i + 1])['relation'] for i in range(len(path) - 1)]
                average_weight = total_weight / (len(path) - 1)

                # Check if all weights meet the threshold
                #for w in weight_list:
                #    if w < 0.05:
                #        flag = False

                # If all weights are valid, add the path to the list
                if flag:
                    paths_with_weights.append({
                        "path": path,
                        "relations": relations,
                        "weights": weight_list,
                        "average_weight": average_weight
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
                "average_weight": path_info["average_weight"]
            })

    result['num_paths'] = min(num_paths, len(paths_with_weights))
    return result
    # Render the HTML template with the result data
    # return render(request, 'path_results.html', {"result": result})
