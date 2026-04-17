import uuid
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from .models import ChatMessage, ChatSession, Document


class DayOneClearFlowsTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_delete_chat_history_only_clears_messages_in_session(self):
		session = ChatSession.objects.create(id=uuid.uuid4())
		ChatMessage.objects.create(session=session, sender="USER", message_text="Q1")
		ChatMessage.objects.create(session=session, sender="AI", message_text="A1")

		response = self.client.delete(f"/api/sessions/{session.id}/messages/delete/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(ChatMessage.objects.filter(session=session).count(), 0)
		self.assertTrue(ChatSession.objects.filter(id=session.id).exists())

	def test_clear_vector_store_deletes_documents_but_keeps_chat_history(self):
		upload = SimpleUploadedFile("demo.pdf", b"dummy", content_type="application/pdf")
		Document.objects.create(file_name="demo.pdf", file_path=upload)

		session = ChatSession.objects.create(id=uuid.uuid4())
		ChatMessage.objects.create(session=session, sender="USER", message_text="Q1")

		response = self.client.delete("/api/admin/vector-store/clear/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Document.objects.count(), 0)
		self.assertEqual(ChatMessage.objects.count(), 1)


class DayTwoCitationPersistenceTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_get_chat_history_returns_sources(self):
		session = ChatSession.objects.create(id=uuid.uuid4())
		expected_sources = [
			{"file_name": "cv.pdf", "page": 1, "content": "Java Spring Boot"},
		]
		ChatMessage.objects.create(
			session=session,
			sender="AI",
			message_text="A1",
			sources=expected_sources,
		)

		response = self.client.get(f"/api/sessions/{session.id}/messages/")

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["messages"][0]["sources"], expected_sources)

	@patch("chat_app.views.ask_documents")
	def test_chat_api_persists_sources_on_ai_message(self, mock_ask_documents):
		mock_ask_documents.return_value = (
			"Tra loi",
			[{"file_name": "cv.pdf", "page": 1, "content": "Redis"}],
		)

		upload = SimpleUploadedFile("demo.pdf", b"dummy", content_type="application/pdf")
		doc = Document.objects.create(file_name="demo.pdf", file_path=upload)

		response = self.client.post(
			"/api/chats/",
			{
				"message": "Hoi thu",
				"document_ids": [str(doc.id)],
			},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		ai_message = ChatMessage.objects.filter(sender="AI").latest("created_at")
		self.assertEqual(ai_message.sources, [{"file_name": "cv.pdf", "page": 1, "content": "Redis"}])



