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


class EntityExtractionView(View):
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

            # 4. 保存结果（CSV + JSONL）
            timestamp = datetime.now().strftime("%Y%m%d")
            result_files = self._save_results(entity_types, relations, timestamp)

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
                        "relations": [[relation[0], relation[1], relation[2]]for relation in item['relations']]
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
        query = prompt % query #, entities_type)
        res = self.query_from_models(query, "DEEPSEEK")

        entity_pattern = r'{(.*?)[:] ?(.*?)}'
        triplet_pattern = r'<(.*?)[,，] ?(.*?)[,，] ?(.*?)>'
        kvs = re.findall(entity_pattern, res, re.DOTALL)
        kvs2 = re.findall(triplet_pattern, res, re.DOTALL)

        return docid, paraid, kvs, kvs2

# 其中可能的實體類型的參考是：
#         %s