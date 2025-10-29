from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_page, name='chatbot_page'),           # Affiche chatbot.html
    # path('response/', views.chatbot_api, name='chatbot_api'),    # API POST pour le chatbot
    path('api/ask/', views.chatbot_api, name='chatbot_api'),

    path('about/', views.about_page, name='about_page'),    
    path('contact/', views.contact_page, name='contact_page')
]
