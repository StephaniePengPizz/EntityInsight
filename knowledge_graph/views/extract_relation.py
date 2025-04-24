import re
import json
import zipfile

from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import requests
import csv
from io import StringIO, BytesIO
from django.http import HttpResponse
from concurrent.futures import as_completed
from knowledge_graph.views.process_to_paragraph import ProcessArticlesView

class EntityExtractionView(View):
    def get(self, request):
        try:
            processed_data = ProcessArticlesView().get_processed_data()
            docid = [item['docid'] for item in processed_data['data']]
            paraid = [item['paraid'] for item in processed_data['data']]
            content_list = [item['content'] for item in processed_data['data']]

            # Limit to first 5 items for demo (remove in production)
            if len(content_list) > 5:
                content_list = content_list[:5]
                docid = docid[:5]
                paraid = paraid[:5]

            entity_types = []
            relations = []

            with ThreadPoolExecutor(max_workers=1) as executor:
                futures = [
                    executor.submit(
                        self.fetch_res_ER_new_DEEPSEEK,
                        d, p, q
                    ) for d, p, q in zip(docid, paraid, content_list)
                ]

                for future in tqdm(as_completed(futures), total=len(futures)):
                    d, p, list1, list2 = future.result()
                    entity_types.append({'docid': d, 'paraid': p, 'entities': list1})
                    relations.append({'docid': d, 'paraid': p, 'relations': list2})

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 实体CSV
                entities_csv = StringIO()
                csv_writer = csv.writer(entities_csv)
                csv_writer.writerow(['DocID', 'ParaID', '实体名称', '实体类型'])
                for item in entity_types:
                    for entity in item['entities']:
                        csv_writer.writerow([item['docid'], item['paraid'], entity[0], entity[1]])
                zip_file.writestr('entities.csv', entities_csv.getvalue())

                # 关系CSV
                relations_csv = StringIO()
                csv_writer = csv.writer(relations_csv)
                csv_writer.writerow(['DocID', 'ParaID', '主体', '关系类型', '客体'])
                for item in relations:
                    for relation in item['relations']:
                        csv_writer.writerow([item['docid'], item['paraid'], relation[0], relation[1], relation[2]])
                zip_file.writestr('relations.csv', relations_csv.getvalue())

            # 设置HTTP响应
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="entity_relations.zip"'
            return response

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def query_from_models(self, message_content, model="DEEPSEEK", max_retries=3):
        API_KEY = 'sk-6df90481a11c4fdd951c090c3369d3dd'.strip()
        API_URL = 'https://api.deepseek.com/v1/chat/completions'
        model_name_map = {
            "DEEPSEEK": "deepseek-chat",
            "openai": "gpt-3.5-turbo",
        }
        model_name = model_name_map.get(model, "deepseek-chat")

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": message_content}],
            "temperature": 0.7,
            "max_tokens": 1500
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                result_json = response.json()
                return result_json['choices'][0]['message']['content']
            except requests.exceptions.RequestException as e:
                print(f"Request failed {attempt + 1}/{max_retries}: {e}")
                time.sleep(3)

        print("Multiple requests failed, giving up")
        return ""

    def get_query_understand(self, query):
        # TODO: Implement or connect to NLP service
        return {"term": []}

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

        prompt = '''
- 角色: 金融行業數據標註專家
- 目標: 提取文章中的金融實體和構建實體關係三元組，同時忽略數值類型的實體，並解釋思考過程
- 限制條件: 
  - 實體類型應限定為：Regulator, Bank, Company, Product, Government, Rating Agency, Financial Infrastructure, Key People
  - 關係應有意義，避免無明確關係的實體對
  - 避免實體未知的情況
- 輸出格式:
  - 實體以「{實體1:實體類型1}」格式輸出
  - 關係三元組以「<實體1, 實體間關係, 實體2>」格式輸出
- 範例:
  實體：{Google:Companies}
  實體：{Android:Product}
  三元組：<Google, 開發, Android>
  
你要處理的新聞內容如下：
%s
  
其中可能的實體類型的參考是：
%s
  
你的輸出是.......'''
        query = prompt % (query, entities_type)
        res = self.query_from_models(query, "DEEPSEEK")

        entity_pattern = r'{(.*?)[:] ?(.*?)}'
        triplet_pattern = r'<(.*?)[,，] ?(.*?)[,，] ?(.*?)>'
        kvs = re.findall(entity_pattern, res, re.DOTALL)
        kvs2 = re.findall(triplet_pattern, res, re.DOTALL)

        return docid, paraid, kvs, kvs2