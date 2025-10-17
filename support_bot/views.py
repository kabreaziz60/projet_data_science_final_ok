# support_bot/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .chatbot_engine import get_response # Importez notre logique

def chatbot_page(request):
    """Affiche la page du chatbot."""
    return render(request, 'support_bot/chatbot.html')

def get_chatbot_response(request):
    """Vue API pour obtenir une réponse du chatbot."""
    if request.method == 'POST':
        # Récupérer le message de l'utilisateur envoyé par AJAX
        user_message = request.POST.get('message', '') 

        # Obtenir la réponse du moteur
        bot_response = get_response(user_message)

        # Retourner la réponse au format JSON
        return JsonResponse({'message': bot_response})

    # Pour toute autre méthode, renvoyer une erreur simple
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)