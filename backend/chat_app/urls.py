from django.urls import path

from . import views

urlpatterns = [
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('chats/', views.chat_with_document, name='chat_with_document'),
    path('sessions/<uuid:session_id>/messages/', views.get_chat_history, name='get_chat_history'),
    path('sessions/', views.get_all_sessions, name='get_all_sessions'),
    path('sessions/<uuid:session_id>/messages/delete/', views.delete_chat_history, name='delete_chat_history'),
    path('sessions/<uuid:session_id>/', views.delete_session, name='delete_session'),
    path('admin/clear-all/', views.clear_all_data, name='clear_all_data'),
    path('admin/vector-store/clear/', views.clear_vector_store, name='clear_vector_store'),
    path('documents/', views.get_documents, name='get_documents'),
    path('documents/rebuild-index/', views.rebuild_faiss_index, name='rebuild_faiss_index'),
]