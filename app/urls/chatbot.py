from django.urls import path
from app.views.chatbot import chat_view

urlpatterns = [
    path("chat/", chat_view, name="chatbot"),
]
