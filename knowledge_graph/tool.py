from collections import deque


def normalize_dict_values(input_dict):
    values = list(input_dict.values())
    min_val = min(values)
    max_val = max(values)
    return {key: (value - min_val) / (max_val - min_val) for key, value in input_dict.items()}

def state_string_trans(before, single):
    temp_list = before.split('@') # 不可以设置成/,*，因为本身三元组关系就有/的情况
    flag = False
    temp_word_before = None
    temp_word_after = None
    for item in temp_list:
        if single in item:
            temp_word_before = item
            #print(temp_word_before)
            if '9' > item[-2] > '0':
                temp_word_after = item[:-2] + str(int(item[-2:]) + 1)
            else:
                temp_word_after = item[:-1] + str(int(item[-1]) + 1)
            flag = True
    if not flag:
        after = before + '@' + single + '1'
    else:
        after = ""
        for item in temp_list:
            if item != temp_word_before:
                after += item + '@'
            else:
                after += temp_word_after + '@'
        after = after[:-1]
        #print(after)
    return after

def state_top3(before_string):
    temp_list = before_string.split('@') # 不可以设置成/，因为本身三元组关系就有/的情况
    before_dict = {}
    for item in temp_list:
        if '9' > item[-2] > '0':
            before_dict[item[:-2]] = int(item[-2:])
        else:
            before_dict[item[:-1]] = int(item[-1])
    sorted_items = sorted(before_dict.items(), key=lambda item: item[1], reverse=True)

    after_string = ""
    for item in sorted_items[:3]:
        after_string += item[0] + '+'
    after_string = after_string[:-1]
    return after_string

def find_all_paths_within_length(graph, source, max_length):
    all_paths = []
    queue = deque([(source, [source])])
    visited = {source}
    while queue:
        (current_node, current_path) = queue.popleft()
        if len(current_path) > max_length:
            continue
        for neighbor in graph.neighbors(current_node):
            if neighbor not in visited:
                new_path = current_path + [neighbor]
                queue.append((neighbor, new_path))
                visited.add(neighbor)
                if len(new_path) <= max_length:
                    all_paths.append(new_path)
    return all_paths