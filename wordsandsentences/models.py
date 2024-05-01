from django.db import models

# Create your models here.


class Topic(models.Model):
    topic_name = models.CharField(max_length=100)
    loc = models.IntegerField()

    class Meta:
        ordering = ["loc"]


class LearningItem(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.deletion.CASCADE)
    jyutping = models.CharField(max_length=100)
    english = models.CharField(max_length=100)
    notes = models.CharField(blank=True, max_length=200)
    loc = models.IntegerField()

    class Meta:
        abstract = True
        ordering = ["loc"]


class Word(LearningItem):
    audio_file = models.FileField(blank=True, null=True)


class Sentence(LearningItem):
    pass