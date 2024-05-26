from django.contrib import admin

from .models import *


class WordInline(admin.TabularInline):
    model = Word
    fields = ("jyutping", "cantonese", "english", "notes", "loc")


class SentenceInline(admin.TabularInline):
    model = Sentence
    fields = ("jyutping", "cantonese", "english", "notes", "loc")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
  inlines = (WordInline, SentenceInline)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
  pass


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
  pass
