import csv
from datetime import datetime
from io import BytesIO, StringIO

from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from .forms import ImportForm, TopicForm, WordForm, SentenceForm
from .models import Topic, Word, Sentence


class IndexView(generic.TemplateView):
    template_name = "wordsandsentences/index.html"


class EditListView(generic.TemplateView):
    template_name = "wordsandsentences/edit/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic_dict = {}
        for topic in Topic.objects.all():
            topic_dict[topic] = {"words": topic.word_set.all(), "sentences": topic.sentence_set.all()}
        context["topic_dict"] = topic_dict
        return context


class TopicCreateView(generic.CreateView):
    template_name = "wordsandsentences/edit/form.html"
    model = Topic
    form_class = TopicForm
    success_url = reverse_lazy("edit_list")


class TopicUpdateView(generic.UpdateView):
    template_name = "wordsandsentences/edit/form.html"
    model = Topic
    form_class = TopicForm
    success_url = reverse_lazy("edit_list")


class TopicDeleteView(generic.DeleteView):
    template_name = "wordsandsentences/edit/delete.html"
    model = Topic
    success_url = reverse_lazy("edit_list")


class WordCreateView(generic.CreateView):
    template_name = "wordsandsentences/edit/form.html"
    model = Word
    form_class = WordForm
    success_url = reverse_lazy("edit_list")

    def get_initial(self):
        initial = super().get_initial()
        initial["topic"] = Topic.objects.get(pk=self.kwargs["topic_pk"])
        return initial


class WordUpdateView(generic.UpdateView):
    template_name = "wordsandsentences/edit/form.html"
    model = Word
    form_class = WordForm
    success_url = reverse_lazy("edit_list")


class WordDeleteView(generic.DeleteView):
    template_name = "wordsandsentences/edit/delete.html"
    model = Word
    success_url = reverse_lazy("edit_list")


class SentenceCreateView(generic.CreateView):
    template_name = "wordsandsentences/edit/form.html"
    model = Sentence
    form_class = SentenceForm
    success_url = reverse_lazy("edit_list")

    def get_initial(self):
        initial = super().get_initial()
        initial["topic"] = Topic.objects.get(pk=self.kwargs["topic_pk"])
        return initial


class SentenceUpdateView(generic.UpdateView):
    template_name = "wordsandsentences/edit/form.html"
    model = Sentence
    form_class = SentenceForm
    success_url = reverse_lazy("edit_list")


class SentenceDeleteView(generic.DeleteView):
    template_name = "wordsandsentences/edit/delete.html"
    model = Sentence
    success_url = reverse_lazy("edit_list")


class ImportView(generic.FormView):
    template_name = "wordsandsentences/import.html"
    form_class = ImportForm
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        if words_csv := form.cleaned_data["words_csv"]:
            csv_rows = list(csv.DictReader(words_csv.file.read().decode('utf-8').splitlines()))
            with transaction.atomic():
                try:
                    # Create topics
                    all_topics = Topic.objects.all()
                    existing_topic_names = list(all_topics.values_list("topic_name", flat=True))
                    next_topic_loc = all_topics.last().loc + 10 if all_topics.exists() else 0
                    for row in csv_rows:
                        if (topic := row["topic"]) not in existing_topic_names:
                            Topic.objects.create(topic_name=topic, loc=next_topic_loc)
                            print(f"Creating topic {topic}")
                            next_topic_loc += 1
                            existing_topic_names.append(topic)
                    # Sort objects by topic
                    words_by_topic = {}
                    sentences_by_topic = {}
                    for row in csv_rows:
                        print(f"Adding row to topic dict: {row}")
                        topic = row["topic"]
                        is_sentence = row["is_sentence"].lower() == "yes"
                        if is_sentence:
                            model_dict = sentences_by_topic
                        else:
                            model_dict = words_by_topic
                        if topic not in model_dict:
                            model_dict[topic] = []
                        model_dict[topic].append(row)
                    # Create objects
                    topic_ids_by_name = {topic.topic_name: topic.id for topic in Topic.objects.all()}
                    for model_class, model_dict in [(Word, words_by_topic), (Sentence, sentences_by_topic)]:
                        existing_objs = model_class.objects.all()
                        objs_to_create = []
                        objs_to_update = []
                        for topic, rows in model_dict.items():
                            existing_objs_for_topic = existing_objs.filter(topic__topic_name=topic)
                            existing_objs_for_topic_by_jyutping = {obj.jyutping: obj for obj in existing_objs_for_topic}
                            jyutping_values = [row["jyutping"] for row in rows]
                            loc = 0
                            # Get existing objects and make sure they maintain their order before we add the new objects.
                            for obj in existing_objs_for_topic.exclude(jyutping__in=jyutping_values):
                                print(f"Setting loc of existing object {obj.jyutping} to {loc}")
                                obj.loc = loc
                                obj.save()
                                loc += 10
                            # Create/update objects in the CSV.
                            for row in rows:
                                if (jyutping := row["jyutping"]) in existing_objs_for_topic_by_jyutping.keys():
                                    print(f"Updating object {jyutping}")
                                    obj = existing_objs_for_topic_by_jyutping[jyutping]
                                    obj.english = row["english"]
                                    obj.notes = row["notes"]
                                    obj.loc = loc
                                    objs_to_update.append(obj)
                                else:
                                    print(f"Creating object {jyutping}")
                                    obj = model_class(topic_id=topic_ids_by_name[topic], jyutping=jyutping, english=row["english"], notes=row["notes"], loc=loc)
                                    objs_to_create.append(obj)
                                loc += 10
                        if objs_to_create:
                            model_class.objects.bulk_create(objs_to_create)
                        if objs_to_update:
                            model_class.objects.bulk_update(objs_to_update, ["english", "notes", "loc"])
                except Exception as e:
                    return render(self.request, self.template_name, {"form": form, "import_error": f"Error in CSV: {e}"})
        if audio_files := form.cleaned_data["audio_files"]:
            with transaction.atomic():
                try:
                    for audio_file in audio_files:
                        file_name = audio_file.name.split(".")[0]
                        try:
                            obj = Word.objects.get(jyutping__iexact=file_name)
                        except Word.DoesNotExist:
                            raise Exception(f"No word found with jyutping '{file_name}'.")
                        print(f"Attaching audio file to {obj}")
                        obj.audio_file = File(audio_file.file, name=audio_file.name)
                        obj.save()
                except Exception as e:
                    return render(self.request, self.template_name, {"form": form, "import_error": f"Error in audio files: {e}"})

        return super().form_valid(form)
    

class WordsExportView(generic.View):
    def get(request, *args, **kwargs):
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=Jyutping words {datetime.now().date().strftime('%d-%m-%Y')}.csv"}
        )
        writer = csv.writer(response)
        writer.writerow(["topic", "jyutping", "english", "notes", "is_sentence"])
        for topic in Topic.objects.all():
            for word in topic.wordset.all():
                writer.writerow([word.topic.topic_name, word.jyutping, word.english, word.notes, "no"])
            for sentence in topic.sentenceset.all():
                writer.writerow([sentence.topic.topic_name, sentence.jyutping, sentence.english, sentence.notes, "no"])
        return response