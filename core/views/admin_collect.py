from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
import requests

@staff_member_required
def admin_web_collection(request):
    if request.method == 'POST':
        try:
            requests.get('http://127.0.0.1:8000/web-collection/collect')
            return JsonResponse({'status': 'success', 'message': 'Collection completed'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'admin.html')