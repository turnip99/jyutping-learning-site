import csv
import os
import random
import re
from datetime import datetime
from io import BytesIO, StringIO

from django.core.files import File
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from .forms import QuizStartForm, ImportForm, TopicForm, WordForm, SentenceForm
from .models import Topic, Word, Sentence
from .utils import get_topic_dict


class IndexView(generic.TemplateView):
    template_name = "wordsandsentences/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topic_dict"] = get_topic_dict(exclude_empty_topics=True)
        return context
    

class QuizView(generic.FormView):
    template_name = "wordsandsentences/quiz_start.html"
    form_class = QuizStartForm

    @staticmethod
    def get_question_type(include_audio):
        question_int = random.randint(0, 150 if include_audio else 99)
        if question_int > 120:
            return "audio_to_tone"
        elif question_int > 99:
            return "audio_to_not_tone"
        if question_int > 75:
            return "j_to_e"
        elif question_int > 55:
            return "e_to_j_buttons"
        elif question_int > 40:
            return "e_to_j_text"
        elif question_int > 26:
            return "topic_to_not_linked_word"
        elif question_int > 12:
            return "sentence_to_missing_word"
        else:
            return "words_to_ordered_sentence"
        
    @staticmethod
    def get_random_word_or_sentence(exclude_word_ids=[], exclude_sentence_ids=[]):
        words = Word.objects.all()
        if exclude_word_ids:
            words = words.exclude(id__in=exclude_word_ids)
        sentences = Sentence.objects.all()
        if exclude_sentence_ids:
            sentences = sentences.exclude(id__in=exclude_sentence_ids)
        word = random.choice(list(words) + list(sentences))
        return word, type(word) == Sentence
    
    @staticmethod
    def get_random_word(exclude_english=[], exclude_jyutping=[], exclude_ids=[], include_tone=None, audio_only=False, single_jyutping_word_only=False):
        words = Word.objects.all()
        if exclude_english or exclude_jyutping:
            words = words.exclude(Q(english__in=exclude_english) | Q(jyutping__in=exclude_jyutping))
        if exclude_ids:
            words = words.exclude(id__in=exclude_ids)
        if audio_only:
            words = words.exclude(audio_file__in=["", None])
        if single_jyutping_word_only:
            words = words.exclude(jyutping__icontains=" ")
        if include_tone:
            words = words.filter(jyutping__icontains=include_tone)
        return random.choice(words)
    
    @staticmethod
    def get_random_sentence(exclude_english=[], exclude_jyutping=[], exclude_ids=[]):
        sentences = Sentence.objects.all()
        if exclude_english or exclude_jyutping:
            sentences = sentences.exclude(Q(english__in=exclude_english) | Q(jyutping__in=exclude_jyutping))
        if exclude_ids:
            sentences = sentences.exclude(id__in=exclude_ids)
        return random.choice(sentences)
    
    def get_incorrect_words(self, correct_word, is_sentence, exclude_ids=[], include_tone=None, audio_only=False, single_jyutping_word_only=False):
        if correct_word:
            exclude_english = [correct_word.english]
            exclude_jyutping = [correct_word.jyutping]
        else:
            exclude_english = []
            exclude_jyutping = []
        incorrect_words = []
        for _i in range(3):
            if is_sentence:
                incorrect_word = self.get_random_sentence(exclude_english=exclude_english, exclude_jyutping=exclude_jyutping, exclude_ids=exclude_ids)
            else:
                incorrect_word = self.get_random_word(exclude_english=exclude_english, exclude_ids=exclude_ids, exclude_jyutping=exclude_jyutping, include_tone=include_tone, audio_only=audio_only, single_jyutping_word_only=single_jyutping_word_only)
            exclude_english.append(incorrect_word.english)
            exclude_jyutping.append(incorrect_word.jyutping)
            incorrect_words.append(incorrect_word)
        return incorrect_words
        
    def form_valid(self, form):
        question_count = int(form.cleaned_data["question_count"])
        include_audio = form.cleaned_data["include_audio"]
        used_word_ids = []
        used_sentence_ids = []
        questions = []

        def generate_question_dict(question_type):
            match question_type:
                case "j_to_e":
                    correct_word, is_sentence = self.get_random_word_or_sentence(exclude_word_ids=used_word_ids, exclude_sentence_ids=used_sentence_ids)
                    if is_sentence:
                        used_sentence_ids.append(correct_word.id)
                    else:
                        used_word_ids.append(correct_word.id)
                    question_audio_url = correct_word.audio_file.url if not is_sentence and correct_word.audio_file and include_audio else None
                    if question_audio_url and random.randint(0, 1) == 1:
                        question_text = f"What is the English translation of this Cantonese word?"
                    else:
                        question_text = f"What is the English translation of '{correct_word.jyutping}'?"
                    incorrect_words = self.get_incorrect_words(correct_word, is_sentence)
                    options = [{"text": word.english, "audio_url": None, "hide_text": False} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": question_audio_url, "correct": correct_word.english, "options": options, "ordering_options": None})
                case "e_to_j_buttons":
                    correct_word, is_sentence = self.get_random_word_or_sentence(exclude_word_ids=used_word_ids, exclude_sentence_ids=used_sentence_ids)
                    if is_sentence:
                        used_sentence_ids.append(correct_word.id)
                    else:
                        used_word_ids.append(correct_word.id)
                    if (option_audio_only := not is_sentence and correct_word.audio_file and include_audio and random.randint(0, 1) == 1):
                        question_text = f"What is the Cantonse word for '{correct_word.english}'?"
                    else:
                        question_text = f"What is the Jyutping representation of '{correct_word.english}'?"
                    incorrect_words = self.get_incorrect_words(correct_word, is_sentence, audio_only=option_audio_only)
                    options = [{"text": word.jyutping, "audio_url": word.audio_file.url if not is_sentence and word.audio_file and include_audio else None, "hide_text": option_audio_only} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word.jyutping, "options": options, "ordering_options": None})
                case "e_to_j_text":
                    correct_word, is_sentence = self.get_random_word_or_sentence(exclude_word_ids=used_word_ids, exclude_sentence_ids=used_sentence_ids)
                    if is_sentence:
                        used_sentence_ids.append(correct_word.id)
                    else:
                        used_word_ids.append(correct_word.id)
                    question_text = f"What is the Jyutping representation of '{correct_word.english}'?"
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word.jyutping, "options": None, "ordering_options": None})
                case "audio_to_tone":
                    word = self.get_random_word(exclude_ids=used_word_ids, audio_only=True, single_jyutping_word_only=True)
                    used_word_ids.append(word.id)
                    question_audio_url = word.audio_file.url
                    question_text = f"What tone is used for these Cantonese word?"
                    options = [{"text": str(tone_num), "audio_url": None, "hide_text": False} for tone_num in [1, 2, 3, 4, 5, 6]]
                    questions.append({"question_text": question_text, "question_audio_url": question_audio_url, "correct": word.jyutping[-1], "options": options, "ordering_options": None})
                case "audio_to_not_tone":
                    correct_word = self.get_random_word(exclude_ids=used_word_ids, audio_only=True)
                    used_word_ids.append(correct_word.id)
                    tones_in_word = set(re.findall(r'\d+', correct_word.jyutping))
                    tones_not_in_word = list(set(["1", "2", "3", "4", "5", "6"]).difference(tones_in_word))
                    excluded_tone = random.choice(tones_not_in_word)
                    question_text = f"Which of these Cantonese words does not use tone {excluded_tone}?"
                    incorrect_words = self.get_incorrect_words(correct_word, False, include_tone=excluded_tone, audio_only=True)
                    options = [{"text": word.jyutping, "audio_url": word.audio_file.url, "hide_text": True} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word.jyutping, "options": options, "ordering_options": None})
                case "topic_to_not_linked_word":
                    topic = random.choice(Topic.objects.all().annotate(word_count=Count("word")).filter(word_count__gte=3))
                    correct_word = self.get_random_word(exclude_ids=list(Word.objects.filter(topic=topic).values_list("id", flat=True)) + used_word_ids)
                    used_word_ids.append(correct_word.id)
                    if (option_audio_only := correct_word.audio_file and include_audio and random.randint(0, 1) == 1 and topic.word_set.exclude(audio_file__in=["", None]).count() >= 3):
                        question_text = f"Which of these Cantonese words are not associated with the topic '{topic.topic_name}'?"
                    else:
                        question_text = f"Which of these Jyutping words are not associated with the topic '{topic.topic_name}'?"
                    incorrect_words = self.get_incorrect_words(correct_word, False, exclude_ids=Word.objects.exclude(topic=topic).values_list("id", flat=True), audio_only=option_audio_only)
                    options = [{"text": word.jyutping, "audio_url": word.audio_file.url if word.audio_file and include_audio else None, "hide_text": option_audio_only} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word.jyutping, "options": options, "ordering_options": None})
                case "sentence_to_missing_word":
                    sentence = self.get_random_sentence(exclude_ids=used_sentence_ids)
                    used_sentence_ids.append(sentence.id)
                    sentence_word_array = sentence.jyutping.split(" ")
                    correct_word_jyutping = random.choice(sentence_word_array).title()
                    question_text = f"Fill in the blank: {' '.join(["_" if sentence_word.title() == correct_word_jyutping else sentence_word for sentence_word in sentence_word_array])}."
                    incorrect_words = self.get_incorrect_words(None, False, exclude_ids=Word.objects.filter(jyutping=correct_word_jyutping).values_list("id", flat=True), single_jyutping_word_only=True)
                    options = [{"text": word_jyutping, "audio_url": None, "hide_text": False} for word_jyutping in [incorrect_word.jyutping for incorrect_word in incorrect_words] + [correct_word_jyutping]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word_jyutping, "options": options, "ordering_options": None})
                case "words_to_ordered_sentence":
                    sentence = self.get_random_sentence(exclude_ids=used_sentence_ids)
                    used_sentence_ids.append(sentence.id)
                    sentence_word_array = sentence.jyutping.split(" ")
                    question_text = f"Order these words to form the Jyutping representation of '{sentence.english}'."
                    sentence_word_array_shuffled = [sentence_word.title() for sentence_word in sentence_word_array]
                    random.shuffle(sentence_word_array_shuffled)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": sentence_word_array, "options": None, "ordering_options": sentence_word_array_shuffled})
                case _:
                    raise Exception(f"Unknown question type {question_type}")
            
        for _question_number in range(question_count):
            for attempt_count in range(5):
                try:
                    generate_question_dict(self.get_question_type(include_audio))
                    break
                except Exception as e:
                    print(e)
                    if attempt_count == 4:
                        raise Exception("Quiz generation failed; try adding more words to the database.")
            
        return render(self.request, "wordsandsentences/quiz.html", {"questions": questions})



class EditListView(generic.TemplateView):
    template_name = "wordsandsentences/edit/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topic_dict"] = get_topic_dict()
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
                            next_topic_loc += 10
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
                        words = Word.objects.filter(jyutping__iexact=file_name)
                        if not words.exists():
                            raise Exception(f"No word found with jyutping '{file_name}'.")
                        for word in words:
                            if word.audio_file and os.path.isfile(word.audio_file.path):
                                os.remove(word.audio_file.path)
                            print(f"Attaching audio file to {word}")
                            word.audio_file = File(audio_file.file, name=audio_file.name)
                            word.save()
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