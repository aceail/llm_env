from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inference', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='inferenceresult',
            name='image_urls',
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.AlterField(
            model_name='inferenceresult',
            name='user_prompt',
            field=models.TextField(blank=True),
        ),
        migrations.RemoveField(
            model_name='inferenceresult',
            name='image_url',
        ),
    ]
