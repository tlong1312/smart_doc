import os

from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Document, ChatSession, ChatMessage
from .rag.ingestion import ingest_file
from .rag.query import ask_documents


# Create your views here.
@api_view(['POST'])
def upload_document(request):
    if 'file' not in request.FILES:
        return Response({"error": "Vui lòng đính kèm file!"}, status=status.HTTP_400_BAD_REQUEST)

    upload_file = request.FILES['file']

    try:
        doc = Document.objects.create(
            file_name=upload_file.name,
            file_path=upload_file
        )

        absolute_file_path = os.path.join(settings.MEDIA_ROOT, str(doc.file_path))

        rag_result = ingest_file(absolute_file_path, str(doc.id))

        if rag_result.get("status") == "success":
            doc.faiss_folder_path = rag_result.get("faiss_path")
            doc.save()

            return Response({
                "message": "Upload và xử lý AI thành công!",
                "document_id": doc.id,
                "file_name": doc.file_name
            }, status=status.HTTP_200_OK)
        else:
            doc.delete()
            return Response({"error": rag_result.get("msg", "Lỗi xử lý AI")}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def chat_with_document(request):
    doc_ids = request.data.get("document_ids", [])
    user_message = request.data.get("message")
    session_id = request.data.get("session_id")

    if not doc_ids or not user_message:
        return Response({"error": "Thiếu document_ids (mảng) hoặc message!"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        docs = Document.objects.filter(id__in=doc_ids)
        if not docs.exists():
            return Response({"error": "Không tìm thấy tài liệu nào hợp lệ!"}, status=status.HTTP_404_NOT_FOUND)

        if session_id:
            session = ChatSession.objects.get(id=session_id)
            for doc in docs:
                session.documents.add(doc)
        else:
            session = ChatSession.objects.create()
            session.documents.set(docs)

        ChatMessage.objects.create(
            session=session,
            sender='USER',
            message_text=user_message
        )

        history_msgs = session.messages.all().order_by('-created_at')[:5]
        history_text = ""
        for msg in reversed(history_msgs):
            sender_name = "Người dùng" if msg.sender == 'USER' else "AI"
            history_text += f"{sender_name}: {msg.message_text}\n"

        absolute_faiss_path = os.path.join(settings.BASE_DIR, 'faiss_index', 'global_index')
        doc_ids_str = [str(d.id) for d in docs]

        ai_response_text, source_list = ask_documents(
            absolute_faiss_path,
            user_message,
            history_text,
            doc_ids_str
        )

        ChatMessage.objects.create(
            session=session,
            sender='AI',
            message_text=ai_response_text
        )

        return Response({
            "session_id": session.id,
            "answer": ai_response_text,
            "sources": source_list
        }, status=status.HTTP_200_OK)
    except Document.DoesNotExist:
        return Response({"error": "Không tìm thấy tài liệu!"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






















