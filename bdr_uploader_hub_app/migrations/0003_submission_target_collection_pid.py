from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bdr_uploader_hub_app', '0002_submission_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='target_collection_pid',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
