from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('evaluation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluation',
            name='lesion_vessel',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='evaluation',
            name='lesion_anatomic',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
