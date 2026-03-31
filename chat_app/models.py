import uuid

from django.db import models

# Create your models here.
class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)

    file_path = models.FileField(upload_to='uploads/')

    faiss_folder_path = models.CharField(max_length=255, blank=True, null=True)

    upload_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session for {self.document.file_name}"

class ChatMessage(models.Model):
    SENDER_CHOICES = (
        ('USER', 'Người dùng'),
        ('AI', 'Trợ lý AI'),
    )
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.message_text[:30]}..."