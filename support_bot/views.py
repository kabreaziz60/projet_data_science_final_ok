from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .chatbot_engine import get_chatbot_response

def chatbot_page(request):
    return render(request, 'chatbot.html')

@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        if request.content_type and "application/json" in request.content_type:
            payload = json.loads(request.body.decode('utf-8'))
            user_input = (payload.get('question') or payload.get('message') or '').strip()
        else:
            user_input = (request.POST.get('message') or request.POST.get('question') or '').strip()
    except Exception:
        user_input = ''

    resp = get_chatbot_response(user_input)
    # on renvoie 2 clés pour compat avant/après
    return JsonResponse({'response': resp, 'answer': resp})

def about_page(request):
    return render(request, 'about.html')  # fichier à créer

def contact_page(request):
    return render(request, 'contact.html')  # fichier à créer



