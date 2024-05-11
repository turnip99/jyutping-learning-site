# Generated by Django 5.0.4 on 2024-05-04 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wordsandsentences', '0002_word_audio_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='topic_name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='sentence',
            unique_together={('topic', 'jyutping')},
        ),
        migrations.AlterUniqueTogether(
            name='word',
            unique_together={('topic', 'jyutping')},
        ),
    ]