from django.urls import path

from . import views

urlpatterns = [
    path('upload/', views.upload_document, name='upload_document'),
    path('chat/', views.chat_with_document, name='chat_with_document'),
    path('history/', views.get_chat_history, name='get_chat_history'),
    path('sessions/', views.get_all_sessions, name='get_all_sessions'),
    path('history/delete/chat/', views.delete_chat_history, name='delete_chat_history'),
    path('history/delete/session/', views.delete_session, name='delete_session'),
    path('clear-all/', views.clear_all_data, name='clear_all_data'),
    path('documents/', views.get_documents, name='get_documents'),
    path('rebuild-index/', views.rebuild_faiss_index, name='rebuild_faiss_index'),
]