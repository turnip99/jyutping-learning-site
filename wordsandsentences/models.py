from django.db import models

# Create your models here.


class Topic(models.Model):
    topic_name = models.CharField(max_length=100, unique=True)
    colour = models.CharField(max_length=7, default="#000000", help_text="Pick a light colour, for good contrast with black text.")
    loc = models.IntegerField()

    class Meta:
        ordering = ["loc"]

    def __str__(self):
        return self.topic_name.capitalize()


class LearningItem(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.deletion.CASCADE)
    jyutping = models.CharField(max_length=100)
    cantonese = models.CharField(blank=True, max_length=50)
    english = models.CharField(max_length=100)
    notes = models.CharField(blank=True, max_length=200)
    loc = models.IntegerField()

    class Meta:
        abstract = True
        ordering = ["loc"]
        unique_together = [["topic", "jyutping"]]

    def __str__(self):
        return f"{self.jyutping} ({self.english})"
    
    @property
    def cantonese_and_jyutping(self):
        return f"{self.jyutping}{f' ({self.cantonese})' if self.cantonese else ''}"


class Word(LearningItem):
    audio_file = models.FileField(blank=True, null=True)


class Sentence(LearningItem):
    response_to = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="responses", help_text="Hold Ctrl to select multiple.")