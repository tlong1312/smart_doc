from django.urls import path

from . import views

urlpatterns = [
    path('upload/', views.upload_document, name='upload_document'),
    path('chat/', views.chat_with_document, name='chat_with_document'),
]