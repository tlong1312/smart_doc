import os
import shutil
import logging
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Document, ChatSession, ChatMessage
from .rag.ingestion import ingest_file
from .rag.query import ask_documents

logger = logging.getLogger(__name__)

@csrf_exempt
def upload_document(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    logger.info(f"=== UPLOAD DOCUMENT ===")
    logger.info(f"FILES keys: {list(request.FILES.keys())}")

    if 'file' not in request.FILES:
        logger.error(f"No 'file' in FILES. Available: {list(request.FILES.keys())}")
        return JsonResponse({
            "error": "Vui lòng đính kèm file!",
            "available_keys": list(request.FILES.keys())
        }, status=400)

    upload_file = request.FILES['file']
    logger.info(f"File received: {upload_file.name}, size: {upload_file.size}")

    try:
        doc = Document.objects.create(
            file_name=upload_file.name,
            file_path=upload_file
        )
        logger.info(f"✅ Document created: {doc.id}")

        absolute_file_path = os.path.join(settings.MEDIA_ROOT, str(doc.file_path))

        try:
            rag_result = ingest_file(absolute_file_path, str(doc.id))
            logger.info(f"RAG result: {rag_result}")

            if rag_result.get("status") == "success":
                doc.faiss_folder_path = rag_result.get("faiss_path")
                doc.save()
                return JsonResponse({
                    "message": "Upload và xử lý AI thành công!",
                    "document_id": str(doc.id),
                    "file_name": doc.file_name
                })
            else:
                logger.warning(f"RAG processing failed but document saved: {rag_result.get('msg')}")
                doc.save()
                return JsonResponse({
                    "message": "File được lưu nhưng xử lý AI chưa hoàn tất. Hãy thử chat để xem thêm thông tin.",
                    "document_id": str(doc.id),
                    "file_name": doc.file_name,
                    "warning": rag_result.get("msg", "Lỗi xử lý AI")
                }, status=202)
        except Exception as rag_error:
            logger.warning(f"RAG ingestion error: {str(rag_error)}. Saving document anyway...")
            doc.save()
            return JsonResponse({
                "message": "File được lưu thành công! (xử lý AI thất bại, nhưng file vẫn được lưu)",
                "document_id": str(doc.id),
                "file_name": doc.file_name,
                "warning": str(rag_error)
            }, status=202)
    except Exception as e:
        logger.exception(f"Exception: {str(e)}")
        return JsonResponse({
            "error": f"Lỗi: {str(e)}"
        }, status=500)

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
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def clear_all_data(request):
    try:
        ChatMessage.objects.all().delete()
        ChatSession.objects.all().delete()
        Document.objects.all().delete()

        uploads_path = os.path.join(settings.BASE_DIR, 'uploads')
        if os.path.exists(uploads_path):
            shutil.rmtree(uploads_path)
        os.makedirs(uploads_path, exist_ok=True)

        global_index_path = os.path.join(settings.BASE_DIR, 'faiss_index', 'global_index')
        if os.path.exists(global_index_path):
            shutil.rmtree(global_index_path)
            logger.info(f"✅ Deleted global_index: {global_index_path}")

        return Response({"message": "Reset success"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_documents(request):
    try:
        documents = Document.objects.all().order_by('-upload_at')
        documents_data = [
            {
                "id": str(doc.id),
                "file_name": doc.file_name,
                "upload_at": doc.upload_at.isoformat()
            }
            for doc in documents
        ]
        return Response({
            "status": "success",
            "total": documents.count(),
            "documents": documents_data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_chat_history(request, session_id):
    try:
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response({
                "error": "Session không tồn tại"
            }, status=status.HTTP_404_NOT_FOUND)

        messages = ChatMessage.objects.filter(session=session).order_by('created_at')

        messages_data = [
            {
                "id": str(msg.id),
                "sender": msg.sender,
                "message": msg.message_text,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]

        return Response({
            "status": "success",
            "session_id": str(session_id),
            "total_messages": len(messages_data),
            "messages": messages_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def rebuild_faiss_index(request):
    try:
        logger.info("=== REBUILD FAISS INDEX ===")
        documents = Document.objects.all()

        if not documents.exists():
            return Response({
                "error": "Không có document nào để rebuild index"
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Rebuilding index for {documents.count()} documents...")

        success_count = 0
        failed_count = 0
        failed_docs = []

        for doc in documents:
            try:
                absolute_file_path = os.path.join(settings.MEDIA_ROOT, str(doc.file_path))

                if not os.path.exists(absolute_file_path):
                    logger.warning(f"File not found: {absolute_file_path}")
                    failed_count += 1
                    failed_docs.append({"id": str(doc.id), "name": doc.file_name, "reason": "File not found"})
                    continue

                rag_result = ingest_file(absolute_file_path, str(doc.id))

                if rag_result.get("status") == "success":
                    doc.faiss_folder_path = rag_result.get("faiss_path")
                    doc.save()
                    success_count += 1
                    logger.info(f"✅ Rebuilt index for: {doc.file_name}")
                else:
                    failed_count += 1
                    failed_docs.append({
                        "id": str(doc.id),
                        "name": doc.file_name,
                        "reason": rag_result.get("msg", "Unknown error")
                    })
                    logger.warning(f"❌ Failed to rebuild index for: {doc.file_name}")
            except Exception as e:
                failed_count += 1
                failed_docs.append({
                    "id": str(doc.id),
                    "name": doc.file_name,
                    "reason": str(e)
                })
                logger.exception(f"❌ Exception rebuilding index for {doc.file_name}: {str(e)}")

        return Response({
            "status": "completed",
            "total": documents.count(),
            "success": success_count,
            "failed": failed_count,
            "failed_documents": failed_docs
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Rebuild index error: {str(e)}")
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_chat_history(request, session_id):

    try:
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response({
                "error": "Session không tồn tại"
            }, status=status.HTTP_404_NOT_FOUND)

        message_count = ChatMessage.objects.filter(session=session).count()

        ChatMessage.objects.filter(session=session).delete()

        logger.info(f"✅ Deleted {message_count} messages from session {session_id}")

        return Response({
            "status": "success",
            "session_id": str(session_id),
            "deleted_messages": message_count,
            "message": "Đã xóa lịch sử chat thành công!"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Delete chat history error: {str(e)}")
        return Response({
            "status": "error",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_session(request, session_id):
    try:

        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response({
                "error": "Session không tồn tại"
            }, status=status.HTTP_404_NOT_FOUND)

        message_count = ChatMessage.objects.filter(session=session).count()

        session.delete()

        logger.info(f"✅ Deleted session {session_id} with {message_count} messages")

        return Response({
            "status": "success",
            "session_id": str(session_id),
            "deleted_messages": message_count,
            "message": "Đã xóa session thành công!"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Delete session error: {str(e)}")
        return Response({
            "status": "error",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_all_sessions(request):
    try:
        sessions = ChatSession.objects.all().order_by('-created_at')

        sessions_data = []
        for session in sessions:
            messages = ChatMessage.objects.filter(session=session)
            documents = session.documents.all()

            sessions_data.append({
                "session_id": str(session.id),
                "created_at": session.created_at.isoformat(),
                "total_messages": messages.count(),
                "total_documents": documents.count(),
                "documents": [
                    {
                        "id": str(doc.id),
                        "file_name": doc.file_name
                    }
                    for doc in documents
                ]
            })

        return Response({
            "status": "success",
            "total_sessions": len(sessions_data),
            "sessions": sessions_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Get all sessions error: {str(e)}")
        return Response({
            "status": "error",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

