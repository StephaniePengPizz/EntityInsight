from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
import requests
import json


@staff_member_required
def admin_web_collection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'collect':
                # Run collection
                response = requests.get('http://127.0.0.1:8000/web-collection/collect')
                return JsonResponse({
                    'status': 'success',
                    'message': 'Collection completed',
                    'details': response.json() if response.status_code == 200 else {'status_code': response.status_code}
                })

            elif action == 'process':
                # Initialize results
                results = {
                    'process_articles': None,
                    'extract_relations': None,
                    'load_relations': None
                }

                # Step 1: Process articles
                response1 = requests.get('http://127.0.0.1:8000/knowledge-graph/process-articles/')
                results['process_articles'] = {
                    'status_code': response1.status_code,
                    'response': response1.json() if response1.status_code == 200 else str(response1.content)
                }
                if response1.status_code != 200:
                    raise Exception(f"Process articles failed: {response1.status_code}")

                # Step 2: Extract relations
                response2 = requests.get('http://127.0.0.1:8000/knowledge-graph/extract-relations/')
                results['extract_relations'] = {
                    'status_code': response2.status_code,
                    'response': response2.json() if response2.status_code == 200 else str(response2.content)
                }
                if response2.status_code != 200:
                    raise Exception(f"Extract relations failed: {response2.status_code}")

                # Step 3: Load relations and construct graph
                response3 = requests.get('http://127.0.0.1:8000/knowledge-graph/load-relations-and-construct-graph')
                results['load_relations'] = {
                    'status_code': response3.status_code,
                    'response': response3.json() if response3.status_code == 200 else str(response3.content)
                }
                if response3.status_code != 200:
                    raise Exception(f"Load relations failed: {response3.status_code}")

                return JsonResponse({
                    'status': 'success',
                    'message': 'All processing steps completed successfully',
                    'details': results
                })

            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e),
                'details': results if 'results' in locals() else None
            }, status=500)

    return render(request, 'admin.html')