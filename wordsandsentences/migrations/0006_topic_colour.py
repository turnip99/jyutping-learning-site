# Generated by Django 5.0.6 on 2024-06-06 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wordsandsentences', '0005_sentence_cantonese_word_cantonese'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='colour',
            field=models.CharField(default='#ffffff', help_text='Pick a dark colour, for good contrast with white backgrounds/text.', max_length=7),
        ),
    ]