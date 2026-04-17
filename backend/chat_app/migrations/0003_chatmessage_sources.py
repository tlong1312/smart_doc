from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat_app", "0002_remove_chatsession_document_chatsession_documents"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="sources",
            field=models.JSONField(blank=True, default=list),
        ),
    ]

