from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import CSV

from .models import *


class CustomImportExportModelAdmin(ImportExportModelAdmin):
  formats = [CSV]


class WordInline(admin.TabularInline):
    model = Word
    fields = ("jyutping", "english", "notes", "loc")


class SentenceInline(admin.TabularInline):
    model = Sentence
    fields = ("jyutping", "english", "notes", "loc")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
  inlines = (WordInline, SentenceInline)


@admin.register(Word)
class WordAdmin(CustomImportExportModelAdmin):
  pass


@admin.register(Sentence)
class SentenceAdmin(CustomImportExportModelAdmin):
  pass
