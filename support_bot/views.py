from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .chatbot_engine import get_chatbot_response

# Vue pour afficher la page HTML du chatbot
def chatbot_page(request):
    return render(request, 'chatbot.html')

# Vue API pour recevoir les requêtes POST et renvoyer une réponse JSON
@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        user_input = request.POST.get('message', '')
        response = get_chatbot_response(user_input)
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
