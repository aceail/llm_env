from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('inference', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inferenceresult',
            name='image_url',
        ),
        migrations.AddField(
            model_name='inferenceresult',
            name='image_urls',
            field=models.JSONField(default=list),
        ),
    ]
