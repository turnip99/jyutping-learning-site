from django.db import models

# Create your models here.


class Topic(models.Model):
    topic_name = models.CharField(max_length=100, unique=True)
    loc = models.IntegerField()

    class Meta:
        ordering = ["loc"]

    def __str__(self):
        return self.topic_name


class LearningItem(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.deletion.CASCADE)
    jyutping = models.CharField(max_length=100)
    english = models.CharField(max_length=100)
    notes = models.CharField(blank=True, max_length=200)
    loc = models.IntegerField()

    class Meta:
        abstract = True
        ordering = ["loc"]
        unique_together = [["topic", "jyutping"]]

    def __str__(self):
        return f"{self.jyutping} ({self.english})"


class Word(LearningItem):
    audio_file = models.FileField(blank=True, null=True)


class Sentence(LearningItem):
    pass