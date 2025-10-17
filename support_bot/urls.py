# support_bot/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_page, name='chatbot_page'),
    path('response/', views.get_chatbot_response, name='get_chatbot_response'),
]