# ChatbotProject/urls.py

from django.contrib import admin
from django.urls import path, include  # ⬅️ Assurez-vous d'importer 'include'

urlpatterns = [
    # Chemin standard pour l'interface d'administration de Django
    path('admin/', admin.site.urls),
    
    # 💥 Lier l'URL racine (/) à notre application support_bot
    # Lorsqu'un utilisateur accède à http://127.0.0.1:8000/, Django 
    # consulte les URLs définies dans support_bot/urls.py.
    path('', include('support_bot.urls')),
]