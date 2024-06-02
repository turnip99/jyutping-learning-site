import codecs
import csv
import os
import random
import re
from datetime import datetime

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic
import unicodecsv

from .forms import FlashcardsStartForm, QuizStartForm, ImportForm, TopicForm, WordForm, SentenceForm
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
        word_count = Word.objects.all().count()
        sentence_count = Sentence.objects.all().count()
        sentences_without_responses_count = Sentence.objects.filter(response_to=None).count()
        if include_audio:
            word_portion = word_count * 0.25 / (word_count * 0.25 + sentence_count)
        else:
            word_portion = word_count * 0.075 / (word_count * 0.075 + sentence_count)
        sentences_without_responses_portion = sentences_without_responses_count / sentence_count
        question_category_random = random.random()
        question_type_random = random.random()
        if question_category_random > 0.65:  # General questions
            if question_type_random > 0.6:
                return "j_to_e"
            elif question_type_random > 0.27:
                return "e_to_j_buttons"
            else:
                return "e_to_j_text"
        question_category_random /= 0.65
        if question_category_random <= word_portion:  # Word questions
            if include_audio:
                if question_type_random > 0.63:
                    return "audio_to_tone"
                elif question_type_random > 0.3:
                    return "audio_to_not_tone"
                else:
                    return "topic_to_not_linked_word"
            else:
                return "topic_to_not_linked_word"
        question_category_random -= word_portion
        if question_category_random <= (1 - sentences_without_responses_portion) / 2:  # Sentence (with responses) questions
            if question_type_random > 0.78:
                return "sentence_to_response_buttons"
            elif question_type_random > 0.5:
                return "sentence_to_response_text"
            elif question_type_random > 0.22:
                return "response_to_sentence_buttons"
            else:
                return "response_to_sentence_text"
        else:  # Sentence questions 
            if question_type_random > 0.67:
                return "sentence_to_missing_word_buttons"
            elif question_type_random > 0.36:
                return "sentence_to_missing_word_text"
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
        sentence_ids_without_responses = list(Sentence.objects.filter(responses=None).values_list("id", flat=True))
        sentence_ids_without_response_to = list(Sentence.objects.filter(response_to=None).values_list("id", flat=True))
        # Filter out sentences where the number of responses/response_to is greater than SENTENCE_COUNT - 3  <- as there are not enough incorrect answers to use.
        sentence_count = Sentence.objects.all().count()
        sentence_ids_with_too_many_responses = list(Sentence.objects.exclude(responses=None).annotate(c=Count('responses')).filter(c__gte=sentence_count - 3).values_list("id", flat=True))
        sentences_ids_with_too_many_response_to = list(Sentence.objects.exclude(response_to=None).annotate(c=Count('response_to')).filter(c__gte=sentence_count - 3).values_list("id", flat=True))

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
                        question_text = f"What is the English translation of '{correct_word.cantonese_and_jyutping}'?"
                    incorrect_words = self.get_incorrect_words(correct_word, is_sentence)
                    options = [{"text": word.english, "cantonese": None, "audio_url": None, "hide_text": False} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
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
                    options = [{"text": word.jyutping, "cantonese": word.cantonese, "audio_url": word.audio_file.url if not is_sentence and word.audio_file and include_audio else None, "hide_text": option_audio_only} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word.jyutping, "options": options, "ordering_options": None})
                case "e_to_j_text":
                    correct_word, is_sentence = self.get_random_word_or_sentence(exclude_word_ids=used_word_ids, exclude_sentence_ids=used_sentence_ids)
                    if is_sentence:
                        correct_qs = Sentence.objects.filter(english=correct_word.english)
                        for c in correct_qs:
                            used_sentence_ids.append(c.id)
                    else:
                        correct_qs = Word.objects.filter(english=correct_word.english)
                        for c in correct_qs:
                            used_word_ids.append(c.id)
                    correct_list = list(correct_qs.values_list("jyutping", flat=True))
                    question_text = f"What is the Jyutping representation of '{correct_word.english}'?"
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_list, "options": None, "ordering_options": None})
                case "audio_to_tone":
                    word = self.get_random_word(exclude_ids=used_word_ids, audio_only=True, single_jyutping_word_only=True)
                    used_word_ids.append(word.id)
                    question_audio_url = word.audio_file.url
                    question_text = f"What tone is used for this word?"
                    options = [{"text": str(tone_num), "cantonese": None, "audio_url": None, "hide_text": False} for tone_num in [1, 2, 3, 4, 5, 6]]
                    questions.append({"question_text": question_text, "question_audio_url": question_audio_url, "correct": word.jyutping[-1], "options": options, "ordering_options": None})
                case "audio_to_not_tone":
                    correct_word = self.get_random_word(exclude_ids=used_word_ids, audio_only=True)
                    used_word_ids.append(correct_word.id)
                    tones_in_word = set(re.findall(r'\d+', correct_word.jyutping))
                    tones_not_in_word = list(set(["1", "2", "3", "4", "5", "6"]).difference(tones_in_word))
                    excluded_tone = random.choice(tones_not_in_word)
                    question_text = f"Which of these does not use tone {excluded_tone}?"
                    incorrect_words = self.get_incorrect_words(correct_word, False, include_tone=excluded_tone, audio_only=True)
                    options = [{"text": word.jyutping, "cantonese": word.cantonese, "audio_url": word.audio_file.url, "hide_text": True} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word.jyutping, "options": options, "ordering_options": None})
                case "topic_to_not_linked_word":
                    # Only include topics with at least three words.
                    topic = random.choice(Topic.objects.all().annotate(word_count=Count("word")).filter(word_count__gte=3))
                    correct_word = self.get_random_word(exclude_ids=list(Word.objects.filter(topic=topic).values_list("id", flat=True)) + used_word_ids)
                    used_word_ids.append(correct_word.id)
                    option_audio_only = correct_word.audio_file and include_audio and random.randint(0, 1) == 1 and topic.word_set.exclude(audio_file__in=["", None]).count() >= 3
                    question_text = f"Which of these is not associated with the topic '{topic.topic_name}'?"
                    incorrect_words = self.get_incorrect_words(correct_word, False, exclude_ids=Word.objects.exclude(topic=topic).values_list("id", flat=True), audio_only=option_audio_only)
                    options = [{"text": word.jyutping, "cantonese": word.cantonese, "audio_url": word.audio_file.url if word.audio_file and include_audio else None, "hide_text": option_audio_only} for word in [incorrect_word for incorrect_word in incorrect_words] + [correct_word]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word.jyutping, "options": options, "ordering_options": None})
                case "sentence_to_response_buttons":
                    if len(set(sentence_ids_without_responses + sentence_ids_with_too_many_responses + used_sentence_ids)) == sentence_count:
                        # Fall back on a basic question if we have run out of words with responses.
                        return generate_question_dict("j_to_e")
                    question_sentence = self.get_random_sentence(exclude_ids=sentence_ids_without_responses + sentence_ids_with_too_many_responses + used_sentence_ids)
                    used_sentence_ids.append(question_sentence.id)
                    question_responses = question_sentence.responses.all()
                    correct_sentence = random.choice(question_responses)
                    question_text = f"Which of these would be a response to '{question_sentence.cantonese_and_jyutping}'?"
                    incorrect_sentences = self.get_incorrect_words(correct_sentence, True, exclude_ids=list(question_responses.values_list("id", flat=True)))
                    options = [{"text": sentence.jyutping, "cantonese": sentence.cantonese, "audio_url": None, "hide_text": False} for sentence in [incorrect_sentence for incorrect_sentence in incorrect_sentences] + [correct_sentence]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_sentence.jyutping, "options": options, "ordering_options": None})
                case "sentence_to_response_text":
                    if len(set(sentence_ids_without_responses + used_sentence_ids)) == sentence_count:
                        return generate_question_dict("j_to_e")
                    question_sentence = self.get_random_sentence(exclude_ids=sentence_ids_without_responses + used_sentence_ids)
                    used_sentence_ids.append(question_sentence.id)
                    question_responses = question_sentence.responses.all()
                    question_text = f"What would be a response to '{question_sentence.cantonese_and_jyutping}'?"
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": list(question_responses.values_list("jyutping", flat=True)), "options": None, "ordering_options": None})
                case "response_to_sentence_buttons":
                    if len(set(sentence_ids_without_response_to + sentences_ids_with_too_many_response_to + used_sentence_ids)) == sentence_count:
                        return generate_question_dict("j_to_e")
                    question_sentence = self.get_random_sentence(exclude_ids=sentence_ids_without_response_to + sentences_ids_with_too_many_response_to + used_sentence_ids)
                    used_sentence_ids.append(question_sentence.id)
                    question_response_to = question_sentence.response_to.all()
                    correct_sentence = random.choice(question_response_to)
                    question_text = f"Which of these would '{question_sentence.cantonese_and_jyutping}' be a response to?"
                    incorrect_sentences = self.get_incorrect_words(correct_sentence, True, exclude_ids=list(question_response_to.values_list("id", flat=True)))
                    options = [{"text": sentence.jyutping, "cantonese": sentence.cantonese, "audio_url": None, "hide_text": False} for sentence in [incorrect_sentence for incorrect_sentence in incorrect_sentences] + [correct_sentence]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_sentence.jyutping, "options": options, "ordering_options": None})
                case "response_to_sentence_text":
                    if len(set(sentence_ids_without_response_to + used_sentence_ids)) == sentence_count:
                        return generate_question_dict("j_to_e")
                    question_sentence = self.get_random_sentence(exclude_ids=sentence_ids_without_response_to + used_sentence_ids)
                    used_sentence_ids.append(question_sentence.id)
                    question_response_to = question_sentence.response_to.all()
                    question_text = f"What would '{question_sentence.cantonese_and_jyutping}' be a response to?"
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": list(question_response_to.values_list("jyutping", flat=True)), "options": None, "ordering_options": None})
                case "sentence_to_missing_word_buttons":
                    sentence = self.get_random_sentence(exclude_ids=used_sentence_ids)
                    used_sentence_ids.append(sentence.id)
                    sentence_word_array = sentence.jyutping.replace("?", "").split(" ")
                    correct_word_index = random.choice(range(len(sentence_word_array)))
                    correct_word_jyutping = sentence_word_array[correct_word_index]
                    question_text = f"""Fill in the blank: '{' '.join(["_" if i == correct_word_index else sentence_word for i, sentence_word in enumerate(sentence_word_array)])}{"?" if "?" in sentence.jyutping else ""}'."""
                    incorrect_words = self.get_incorrect_words(None, False, exclude_ids=Word.objects.filter(jyutping=correct_word_jyutping).values_list("id", flat=True), single_jyutping_word_only=True)
                    options = [{"text": word_jyutping, "audio_url": None, "hide_text": False} for word_jyutping in [incorrect_word.jyutping for incorrect_word in incorrect_words] + [correct_word_jyutping]]
                    random.shuffle(options)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": correct_word_jyutping, "options": options, "ordering_options": None})
                case "sentence_to_missing_word_text":
                    sentence = self.get_random_sentence(exclude_ids=used_sentence_ids)
                    used_sentence_ids.append(sentence.id)
                    sentence_word_array = sentence.jyutping.replace("?", "").split(" ")
                    correct_word_index = random.choice(range(len(sentence_word_array)))
                    correct_word_jyutping = sentence_word_array[correct_word_index]
                    question_text = f"""Fill in the blank: '{' '.join(["_" if i == correct_word_index else sentence_word for i, sentence_word in enumerate(sentence_word_array)])}{"?" if "?" in sentence.jyutping else ""}'."""
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": [correct_word_jyutping], "options": None, "ordering_options": None})
                case "words_to_ordered_sentence":
                    sentence = self.get_random_sentence(exclude_ids=used_sentence_ids)
                    used_sentence_ids.append(sentence.id)
                    sentence_word_array = sentence.jyutping.replace("?", "").split(" ")
                    question_text = f"Order these words to form the Jyutping representation of '{sentence.english}'."
                    sentence_word_array_shuffled = [sentence_word for sentence_word in sentence_word_array]
                    random.shuffle(sentence_word_array_shuffled)
                    questions.append({"question_text": question_text, "question_audio_url": None, "correct": sentence_word_array, "options": None, "ordering_options": sentence_word_array_shuffled, "include_question_mark": "?" in sentence.jyutping})
                case _:
                    raise Exception(f"Unknown question type {question_type}")
            
        for _question_number in range(question_count):
            if settings.DEBUG:
                generate_question_dict(self.get_question_type(include_audio))
            else:
                for attempt_count in range(5):
                    try:
                        generate_question_dict(self.get_question_type(include_audio))
                        break
                    except Exception as _e:
                        if attempt_count == 4:
                            raise Exception("Quiz generation failed; try adding more words to the database.")
            
        return render(self.request, "wordsandsentences/quiz.html", {"questions": questions})
    

class FlashcardsView(generic.FormView):
    template_name = "wordsandsentences/flashcards_start.html"
    form_class = FlashcardsStartForm

    def form_valid(self, form):
        topic = form.cleaned_data["topic"]
        randomise_order = form.cleaned_data["randomise_order"]
        words_sentences_both = form.cleaned_data["words_sentences_both"]
        starting_side = form.cleaned_data["starting_side"]
        if words_sentences_both == "sentences":
            words = Word.objects.none()
        else:
            words = Word.objects.all()
        if words_sentences_both == "words":
            sentences = Sentence.objects.none()
        else:
            sentences = Sentence.objects.all()
        if topic:
            words = words.filter(topic=topic)
            sentences = sentences.filter(topic=topic)
        words_and_sentences = list(words) + list(sentences)
        if randomise_order:
            random.shuffle(words_and_sentences)
        return render(self.request, "wordsandsentences/flashcards.html", {"words_and_sentences": words_and_sentences, "starting_side": starting_side})



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

    def get_initial(self):
        initial = super().get_initial()
        if last_topic := Topic.objects.all().last():
            initial["loc"] = last_topic.loc + 10
        else:
            initial["loc"] = 0
        return initial


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
        if last_word := Word.objects.filter(topic_id=self.kwargs["topic_pk"]).last():
            initial["loc"] = last_word.loc + 10
        else:
            initial["loc"] = 0
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
        if last_sentence := Sentence.objects.filter(topic_id=self.kwargs["topic_pk"]).last():
            initial["loc"] = last_sentence.loc + 10
        else:
            initial["loc"] = 0
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.responses.set(form.cleaned_data["responses"])
        self.object.save()
        return response


class SentenceUpdateView(generic.UpdateView):
    template_name = "wordsandsentences/edit/form.html"
    model = Sentence
    form_class = SentenceForm
    success_url = reverse_lazy("edit_list")

    def get_initial(self):
        initial = super().get_initial()
        initial["responses"] = self.object.responses.all()
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.responses.set(form.cleaned_data["responses"])
        self.object.save()
        return response


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
            csv_rows = list(csv.DictReader(words_csv.file.read().decode('utf-8-sig').splitlines()))
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
                                    obj.cantonese = row["cantonese"]
                                    obj.english = row["english"]
                                    obj.notes = row["notes"]
                                    obj.loc = loc
                                    objs_to_update.append(obj)
                                else:
                                    print(f"Creating object {jyutping}")
                                    obj = model_class(topic_id=topic_ids_by_name[topic], jyutping=jyutping, cantonese=row["cantonese"], english=row["english"], notes=row["notes"], loc=loc)
                                    objs_to_create.append(obj)
                                loc += 10
                        if objs_to_create:
                            model_class.objects.bulk_create(objs_to_create)
                        if objs_to_update:
                            model_class.objects.bulk_update(objs_to_update, ["cantonese", "english", "notes", "loc"])
                    for topic, sentence_rows in sentences_by_topic.items():
                        for sentence_row in sentence_rows:
                            if sentence_row["response_to"]:
                                response_to_obj_list = []
                                for response_to in sentence_row["response_to"].replace(", ", ",").split(","):
                                    try:
                                        response_to_obj = Sentence.objects.get(jyutping=response_to)
                                    except Sentence.MultipleObjectsReturned:
                                        response_to_obj = Sentence.objects.get(topic__topic_name=topic, jyutping=response_to)
                                    response_to_obj_list.append(response_to_obj)
                                Sentence.objects.get(topic__topic_name=topic, jyutping=sentence_row["jyutping"]).response_to.set(response_to_obj_list)
                                
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
        response.write(codecs.BOM_UTF8)  # Force into UTF-8 so that it accepts Chinese characters.
        writer = unicodecsv.writer(response)
        writer.writerow(["topic", "jyutping", "cantonese", "english", "notes", "is_sentence", "response_to"])
        for topic in Topic.objects.all():
            for word in topic.word_set.all():
                writer.writerow([word.topic.topic_name, word.jyutping, word.cantonese, word.english, word.notes, "no", ""])
            for sentence in topic.sentence_set.all():
                writer.writerow([sentence.topic.topic_name, sentence.jyutping, sentence.cantonese, sentence.english, sentence.notes, "yes", ", ".join([response_to_sentence.jyutping for response_to_sentence in sentence.response_to.all()])])
        return response