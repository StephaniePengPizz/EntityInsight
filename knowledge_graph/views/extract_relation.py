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

from core.models import NewsArticle

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

            demo_limit = 60
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
                d, p, entities, rels, category = future.result()
                entity_types.append({'doc_id': d, 'para_id': p, 'entities': entities})

                # Add relations with their original paragraph categories
                new_content = []
                for item in rels:
                    new_content.append(item['content'])
                relations.append({'doc_id': d, 'para_id': p, 'content': new_content, 'category': category})

        # Determine dominant category per document
        for doc_id, votes in self.category_votes.items():
            dominant_category = max(votes.items(), key=lambda x: x[1])[0]
            article = NewsArticle.objects.get(id=int(doc_id[0]))  # Assuming doc_id matches article ID
            article.category = dominant_category
            print(dominant_category)
            article.save()
        return entity_types, relations

    def _save_results(self, entity_types, relations, timestamp):
        """保存结果到CSV和JSONL格式"""
        os.makedirs(self.OUTPUT_DIR_ENTITY, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR_RELATION, exist_ok=True)

        # 定义文件路径
        file_paths = {
            'entities_csv': os.path.join(self.OUTPUT_DIR_ENTITY, f'entities_{timestamp}.csv'),
            'pure_entities_txt': os.path.join(self.OUTPUT_DIR_ENTITY, f'pure_entities_{timestamp}.txt'),
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
        with open(file_paths['entities_json'], 'w', encoding='utf-8') as f_json, \
                open(file_paths['pure_entities_txt'], 'w', encoding='utf-8') as f_txt:
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

            json.dump(result, f_json, ensure_ascii=False, indent=2)
            for _, entities in categorized_entities.items():
                if entities:
                    f_txt.write("\n".join(entities) + "\n")

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

    def fetch_res_ER_new_DEEPSEEK(self, doc_id, para_id, query):
        prompt = """
        Role: Financial Data Annotation Specialist
        Objective: 
        1. Classify the article into one primary category
        2. Extract financial entities and construct entity-relationship triples

        Article Categories (choose one primary category):
        - payments
        - markets 
        - retail
        - wholesale
        - wealth
        - regulation
        - crime
        - crypto
        - security
        - startups
        - sustainable
        - ai

        Entity Type Constraints:
        - Regulator, Bank, Company, Product, Government, Rating Agency, Financial Infrastructure, Key People

        Output Format:
        - Start with: 「Category: [selected_category]」
        - Entities: 「{entity1:EntityType1}」
        - Relationship triples: 「<entity1, relationship, entity2>」

        Example:
        Category: [payments]
        Entity: {Google:Company}
        Entity: {Android:Product}
        Triple: <Google, develops, Android>

        The news content you need to process:
        %s

        Your output is...
        """
        query = prompt % query
        res = self.query_from_models(query, "DEEPSEEK")

        # Extract category
        category_match = re.search(r'\[(.*?)\]', res)
        category = category_match.group(1).strip().lower() if category_match else 'unknown'
        #print(res, category)
        # Count category votes per document
        if doc_id not in self.category_votes:
            self.category_votes[doc_id] = {}
        self.category_votes[doc_id][category] = self.category_votes[doc_id].get(category, 0) + 1
        # Extract entities and relations
        entity_pattern = r'{(.*?)[:] ?(.*?)}'
        triplet_pattern = r'<(.*?)[,，] ?(.*?)[,，] ?(.*?)>'
        kvs = re.findall(entity_pattern, res, re.DOTALL)
        kvs2 = re.findall(triplet_pattern, res, re.DOTALL)

        raw_relations = [{'doc_id': doc_id, 'para_id': para_id, 'content': list(k), 'category': category} for k in kvs2]

        cleaned_relations, cleaned_entities = self.clean_relations(raw_relations)

        return doc_id, para_id, kvs, cleaned_relations, category