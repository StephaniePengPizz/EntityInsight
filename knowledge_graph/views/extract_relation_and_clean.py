import os
import glob
import json
import zipfile
import re
from datetime import datetime
from io import StringIO, BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import requests
import csv
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.conf import settings
from dotenv import load_dotenv

from core.constants import entity_types, entity_type

load_dotenv()
API_KEY = os.getenv('DEEPSEEK_API_KEY')

import os
import glob
import json
import csv
from io import StringIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from django.http import JsonResponse
from django.views import View
from django.conf import settings


class CleanEntityExtractionView(View):
    OUTPUT_DIR_RELATION = os.path.join(settings.MEDIA_ROOT, 'relation_extraction')
    OUTPUT_DIR_ENTITY = os.path.join(settings.MEDIA_ROOT, 'entity_extraction')

    def get(self, request):
        try:
            # 1. 查找并加载最新的JSON文件
            json_dir = os.path.join(settings.MEDIA_ROOT, 'processed_articles')
            json_files = glob.glob(os.path.join(json_dir, 'processed_articles_*.json'))

            if not json_files:
                return JsonResponse({'error': 'No processed articles files found'}, status=404)

            latest_file = max(json_files, key=os.path.getmtime)
            processed_data = self._load_json_file(latest_file)

            # 2. 处理数据
            docid = [item['doc_id'] for item in processed_data['data']]
            paraid = [item['para_id'] for item in processed_data['data']]
            content_list = [item['content'] for item in processed_data['data']]

            # 演示限制（生产环境应移除）
            demo_limit = 5
            if len(content_list) > demo_limit:
                content_list = content_list[:demo_limit]
                docid = docid[:demo_limit]
                paraid = paraid[:demo_limit]

            # 3. 提取实体和关系
            entity_types, relations = self._process_entities_relations(docid, paraid, content_list)

            print("1234")
            # 4. 保存结果（CSV + JSONL）
            timestamp = datetime.now().strftime("%Y%m%d")
            result_files = self._save_results(entity_types, relations, timestamp)
            print("5678")
            return JsonResponse({
                'status': 'success',
                'files': result_files,
                'download_links': [
                    {'name': '实体列表 (CSV)', 'url': result_files['entities_csv']},
                    {'name': '关系列表 (CSV)', 'url': result_files['relations_csv']},
                    {'name': '实体列表 (JSONL)', 'url': result_files['entities_json']},
                    {'name': '关系列表 (JSONL)', 'url': result_files['relations_json']}
                ]
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _load_json_file(self, filepath):
        """加载JSON文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _process_entities_relations(self, docid, paraid, content_list):
        """使用线程池处理实体和关系"""
        entity_types = []
        relations = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    self.fetch_res_ER_new_DEEPSEEK,
                    d, p, q
                ) for d, p, q in zip(docid, paraid, content_list)
            ]

            for future in tqdm(as_completed(futures), total=len(futures)):
                d, p, entities, rels = future.result()
                entity_types.append({'doc_id': d, 'para_id': p, 'entities': entities})
                relations.append({'doc_id': d, 'para_id': p, 'relations': rels})

        return entity_types, relations

    def _save_results(self, entity_types, relations, timestamp):
        """保存结果到CSV和JSONL格式"""
        os.makedirs(self.OUTPUT_DIR_ENTITY, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR_RELATION, exist_ok=True)

        # 定义文件路径
        file_paths = {
            'entities_csv': os.path.join(self.OUTPUT_DIR_ENTITY, f'entities_{timestamp}.csv'),
            'relations_csv': os.path.join(self.OUTPUT_DIR_RELATION, f'relations_{timestamp}.csv'),
            'entities_json': os.path.join(self.OUTPUT_DIR_ENTITY, f'entities_{timestamp}.json'),
            'relations_json': os.path.join(self.OUTPUT_DIR_RELATION, f'relations_{timestamp}.json')
        }

        # 保存实体数据
        self._save_entities(entity_types, file_paths)

        # 保存关系数据
        self._save_relations(relations, file_paths)

        # 返回可访问的URL路径
        return {
            'entities_csv': f'/media/entity_extraction_results/{os.path.basename(file_paths["entities_csv"])}',
            'relations_csv': f'/media/entity_extraction_results/{os.path.basename(file_paths["relations_csv"])}',
            'entities_json': f'/media/entity_extraction_results/{os.path.basename(file_paths["entities_json"])}',
            'relations_json': f'/media/entity_extraction_results/{os.path.basename(file_paths["relations_json"])}'
        }

    def _save_entities(self, entity_types, file_paths):
        """保存实体数据"""
        # CSV格式
        with open(file_paths['entities_csv'], 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['DocID', 'ParaID', 'Entity', 'Type'])
            for item in entity_types:
                for entity in item['entities']:
                    writer.writerow([item['doc_id'], item['para_id'], entity[0], entity[1]])

        # JSON
        with open(file_paths['entities_json'], 'w', encoding='utf-8') as f:
            # 初始化分类容器
            categorized_entities = {
                "Regulator": [],
                "Bank": [],
                "Company": [],
                "Product": [],
                "Government": [],
                "Rating Agency": [],
                "Financial Infrastructure": [],
                "Key People": [],
            }

            # 分类统计
            for item in entity_types:
                for entity in item['entities']:
                    entity_name = entity[0]
                    entity_type = entity[1]
                    if entity_type == "Regulator":
                        categorized_entities["Regulator"].append(entity_name)
                    elif entity_type == "Bank":
                        categorized_entities["Bank"].append(entity_name)
                    elif entity_type == "Regulator":
                        categorized_entities["Regulators"].append(entity_name)
                    elif entity_type == "Concept":
                        categorized_entities["Concept"].append(entity_name)
                    elif entity_type == "Event":
                        categorized_entities["Event"].append(entity_name)
                    elif entity_type == "Product":
                        categorized_entities["Product"].append(entity_name)
                    elif entity_type == "Financial Infrastructure":
                        categorized_entities["Financial Infrastructure"].append(entity_name)
                    elif entity_type == "Key People":
                        categorized_entities["Key People"].append(entity_name)
                    elif entity_type == "Rating Agency":
                        categorized_entities["Rating Agency"].append(entity_name)
                    elif entity_type == "Government":
                        categorized_entities["Government"].append(entity_name)
                    elif entity_type == "Company":
                        categorized_entities["Company"].append(entity_name)
                    else:
                        # 默认归类到Industry
                        categorized_entities["Industry"].append(entity_name)

            # 构建结果结构
            result = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "entity_counts": {k: len(v) for k, v in categorized_entities.items()}
                },
                "data": {
                    **categorized_entities,  # 展开分类数据
                    "raw_records": [  # 保留原始记录以便追溯
                        {
                            "doc_id": item['doc_id'],
                            "para_id": item['para_id'],
                            "entities": [
                                {"name": e[0], "type": e[1]}
                                for e in item['entities']
                            ]
                        }
                        for item in entity_types
                    ]
                }
            }

            json.dump(result, f, ensure_ascii=False, indent=2)

    def _save_relations(self, relations, file_paths):
        """保存关系数据"""
        # CSV格式
        with open(file_paths['relations_csv'], 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['DocID', 'ParaID', 'Subject', 'Relation', 'Object'])
            for item in relations:
                for relation in item['relations']:
                    writer.writerow([item['doc_id'], item['para_id'], relation[0], relation[1], relation[2]])

        # JSON
        with open(file_paths['relations_json'], 'w', encoding='utf-8') as f:
            result = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_relations": sum(len(item['relations']) for item in relations)
                },
                "data": [
                    {
                        "doc_id": item['doc_id'],
                        "para_id": item['para_id'],
                        "relations": [[relation[0], relation[1], relation[2]] for relation in item['relations']]
                    }
                    for item in relations
                ]
            }
            json.dump(result, f, ensure_ascii=False, indent=2)

    def query_from_models(self, message_content, model="DEEPSEEK", max_retries=3):
        """Query the DeepSeek API"""
        API_URL = 'https://api.deepseek.com/v1/chat/completions'
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message_content}],
            "temperature": 0.7,
            "max_tokens": 1500
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
            except requests.exceptions.RequestException as e:
                print(f"Request failed {attempt + 1}/{max_retries}: {e}")
                time.sleep(3)

        raise Exception("API request failed after multiple retries")

    def get_entity_type(self, query):
        query_entity_tup = []
        try:
            res = self.get_query_understand(query)
            for term in res['term']:
                should_term = []
                main_word = ''
                for token in term:
                    if token['type']:
                        if 'stock' in token['type'] or 'concept' in token['type'] or 'product' in token[
                            'type'] or 'industry' in token['type']:
                            if 'synonym' in token and token['synonym']: continue
                            query_entity_tup.append((query, token['word'], token['type']))
            return query_entity_tup
        except:
            return []

    def get_types(self, query):
        entity_types = []
        for item in query:
            for entity_type in item['name']:
                entity_types.append(entity_type)
        return entity_types

    def clean_relations(self, relations):
        pattern = r'\{(\w+[:：]\w+)\}'
        pattern2 = r'三元组'

        def special_type(s):
            if 'concept' or 'incident' in s or 'year' in s or 'unknown' in s or 'date' in s:
                return True
            return False

        ans = []
        for item in tqdm(relations, desc="Cleaning relations"):
            for rel_tup in item['content']:
                entity1 = rel_tup[0]
                relation = rel_tup[1]
                entity2 = rel_tup[2]
                new_entity1 = entity1.replace('\n', '')
                new_relation = relation.replace('\n', '')
                new_entity2 = entity2.replace('\n', '')

                match1 = re.search(pattern, new_entity1)
                match2 = re.search(pattern, new_relation)
                match3 = re.search(pattern, new_entity2)
                match4 = re.search(pattern2, new_entity1)

                if match1 and (special_type(new_entity1)):
                    tagged_string = match1.group(1)
                    try:
                        new_entity1, _ = tagged_string.split(':')
                    except:
                        new_entity1, _ = tagged_string.split('：')

                if match2:
                    tagged_string = match2.group(1)
                    try:
                        new_relation, _ = tagged_string.split(':')
                    except:
                        new_relation, _ = tagged_string.split('：')

                if match3 and (special_type(new_entity2)):
                    tagged_string = match3.group(1)
                    try:
                        new_entity2, _ = tagged_string.split(':')
                    except:
                        new_entity2, _ = tagged_string.split('：')

                if match4:
                    index = new_entity1.find('Triple')
                    new_entity1 = new_entity1[index + 5:]

                ans.append({'docid': item['docid'], 'paraid': item['paraid'],
                            'content': [new_entity1, new_relation, new_entity2]})

        def process_tup(original):
            new = []
            pattern2 = r'Triple'
            for item in tqdm(original, desc="Processing triple tags"):
                rel_tup = item['content']
                entity1 = rel_tup[0]
                relation = rel_tup[1]
                entity2 = rel_tup[2]
                new_entity1 = entity1
                new_relation = relation
                new_entity2 = entity2
                match = re.search(pattern2, new_entity1)
                if match:
                    index = new_entity1.find('Triple')
                    new_entity1 = new_entity1[index + 5:]
                new.append({'docid': item['docid'], 'paraid': item['paraid'],
                            'content': [new_entity1, new_relation, new_entity2]})
            return new

        ans2 = process_tup(ans)
        ans3 = process_tup(ans2)

        ans4 = []
        for item in tqdm(ans3, desc="Cleaning belong and located relations"):
            rel_tup = item['content']
            if (rel_tup[1] == 'belongs to' or rel_tup[1] == 'is' or rel_tup[1] == 'are') and rel_tup[2] in entity_type:
                continue
            ans4.append({'docid': item['docid'], 'paraid': item['paraid'], 'content': rel_tup})

        eset_dir = os.path.join(settings.MEDIA_ROOT, 'entity_other')
        eset_file = os.path.join(eset_dir, 'entity_non.txt')  # 直接拼接路径（不依赖glob）

        try:
            with open(eset_file, 'r', encoding='utf-8') as f:
                eset = {line.strip() for line in f if line.strip()}
                print(f"✅ 成功加载 {len(eset)} 个非实体词")
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试其他编码
            with open(eset_file, 'r', encoding='gbk') as f:
                eset = {line.strip() for line in f if line.strip()}
                print(f"✅ 用GBK编码加载 {len(eset)} 个非实体词")
        except Exception as e:
            raise RuntimeError(f"文件读取失败: {eset_file} | 错误: {e}")


        def is_non_entity(s):
            if s in eset: return True
            if s == "" or len(s) == 0: return True
            if (
                    'thought process' in s or
                    'independent entity' in s or
                    'no clear' in s or
                    'not mentioned' in s or
                    'irrelevant' in s or
                    'no specific' in s or
                    'unspecified' in s or
                    'no concrete' in s or
                    'no obvious' in s or
                    'unable to' in s or
                    'no particular' in s or
                    'no entity' in s or
                    'no entities' in s or
                    'entity type' in s or
                    'unknown' in s or
                    'entity:' in s or
                    'entity：' in s  # full-width colon
            ):
                return True
            return False

        ans5 = []
        for item in tqdm(ans4, desc="Removing non-entities"):
            rel_tup = item['content']
            if is_non_entity(rel_tup[0]) or is_non_entity(rel_tup[2]):
                continue
            ans5.append({'docid': item['docid'], 'paraid': item['paraid'], 'content': rel_tup})

        def is_number(s):
            # Match pure numbers, optional + - prefix or suffix
            if re.fullmatch(r'[+-]?\d+(\.\d+)?[+-]?', s.strip()):
                return True

            # Match numbers with English units: 100 USD, 3 years, 5x, 2%, 1.2 billion, 500k, etc.
            if re.search(
                    r'\b[+-]?\d+(\.\d+)? *(USD|EUR|GBP|HKD|percent|%|x|X|times|years?|months?|days?|billion|million|k|K)\b',
                    s, re.IGNORECASE):
                return True

            # Match financial or quarterly formats: Q1 2023, 2022 Q4, H1 2022-H2 2023, FY2022
            if re.search(r'\b(FY)?\d{4}( ?(Q[1-4]|H[1-2]))?(-\d{4}( ?(Q[1-4]|H[1-2]))?)?\b', s, re.IGNORECASE):
                return True

            return False

        ans6 = []
        for item in tqdm(ans5, desc="Removing numerical entities"):
            rel_tup = item['content']
            if is_number(rel_tup[0]) or is_number(rel_tup[2]):
                continue
            ans6.append({'docid': item['docid'], 'paraid': item['paraid'], 'content': rel_tup})

        ans7 = []
        for item in tqdm(ans6, desc="Removing identical entity pairs"):
            rel_tup = item['content']
            if rel_tup[0] == rel_tup[2]:
                continue
            ans7.append({'docid': item['docid'], 'paraid': item['paraid'], 'content': rel_tup})

        def remove_quotes_if_present(s):
            if (s.startswith(("'", '"', '‘', '“')) and s.endswith(("'", '"', '’', '”'))):
                return s[1:-1]
            else:
                return s

        ans8 = []
        for item in tqdm(ans7, desc="Removing quotes from entities"):
            rel_tup = item['content']
            rel_tup_after1 = remove_quotes_if_present(rel_tup[0])
            rel_tup_after2 = remove_quotes_if_present(rel_tup[2])
            ans8.append({'docid': item['docid'], 'paraid': item['paraid'],
                         'content': [rel_tup_after1, rel_tup[1], rel_tup_after2]})

        def is_all_english_letters(s):
            pattern = r'^[a-zA-Z]+'
            return bool(re.match(pattern, s))

        relation_clean_list = []
        new_entities_from_relations = []

        for item in tqdm(ans8, desc="Removing English only relations"):
            rel_tup = item['content']
            if is_all_english_letters(rel_tup[1]):
                continue
            relation_clean_list.append({'docid': item['docid'], 'paraid': item['paraid'], 'content': rel_tup})
            new_entities_from_relations.append(rel_tup[0])
            new_entities_from_relations.append(rel_tup[2])

        new_entities_from_relations = list(set(new_entities_from_relations))

        return relation_clean_list, new_entities_from_relations

    def fetch_res_ER_new_DEEPSEEK(self, docid, paraid, query):
        response = self.get_entity_type(query)
        entities_type = self.get_types(response)

        prompt = """
        Role: Financial Data Annotation Specialist
        Objective: Extract financial entities from articles and construct entity-relationship triples, while ignoring numerical entities. Explain the reasoning process.

        Constraints:
        - Entity types must be limited to: Regulator, Bank, Company, Product, Government, Rating Agency, Financial Infrastructure, Key People
        - Relationships must be meaningful - avoid pairing entities without clear relationships
        - Avoid cases where entities are unknown

        Output Format:
        - Entities in format: 「{entity1:EntityType1}」
        - Relationship triples in format: 「<entity1, relationship, entity2>」

        Example:
        Entity: {Google:Company}
        Entity: {Android:Product}
        Triple: <Google, develops, Android>

        The news content you need to process:
        %s

        Your output is...
        """
        query = prompt % query  # , entities_type)
        res = self.query_from_models(query, "DEEPSEEK")

        entity_pattern = r'{(.*?)[:] ?(.*?)}'
        triplet_pattern = r'<(.*?)[,，] ?(.*?)[,，] ?(.*?)>'
        kvs = re.findall(entity_pattern, res, re.DOTALL)
        kvs2 = re.findall(triplet_pattern, res, re.DOTALL)

        # 包装成统一结构方便清洗使用
        raw_relations = [{'docid': docid, 'paraid': paraid, 'content': list(k)} for k in kvs2]
        print(raw_relations)
        # 调用清洗函数
        cleaned_relations, cleaned_entities = self.clean_relations(raw_relations)
        print(cleaned_relations)
        print(cleaned_entities)
        return docid, paraid, kvs, cleaned_relations

# 其中可能的實體類型的參考是：
#         %s