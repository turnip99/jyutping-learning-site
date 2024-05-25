from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Div, Submit
from django.urls import reverse_lazy

from jyutpinglearningsite.forms import FormWithHelperMixin
from .models import Topic, LearningItem, Word, Sentence


class QuizStartForm(FormWithHelperMixin, forms.Form):
    question_count = forms.ChoiceField(choices=((10, "10"), (25, "25"), (50, "50")), label="Number of questions")
    include_audio = forms.BooleanField(initial=True, label="Include questions with audio", required=False)
    submit_text = "Start quiz"
    submit_css_class = "btn-primary"

    def clean_question_count(self):
        question_count = self.cleaned_data["question_count"]
        if int(question_count) > Word.objects.count() + Sentence.objects.count():
            raise forms.ValidationError("You do not have enough words and sentences in the database for a quiz of this length.")
        return question_count


class TopicForm(FormWithHelperMixin, forms.ModelForm):
    class Meta:
        model = Topic
        fields = [
            "topic_name",
            "loc",
        ]



class LearningItemForm(FormWithHelperMixin, forms.ModelForm):
    class Meta:
        abstract = True
        model = LearningItem
        fields = [
            "topic",
            "jyutping",
            "english",
            "notes",
            "loc",
        ]


class WordForm(LearningItemForm):
    class Meta(LearningItemForm.Meta):
        abstract = False
        model = Word
        fields = LearningItemForm.Meta.fields + ["audio_file"]


class SentenceForm(LearningItemForm):
    responses = forms.ModelMultipleChoiceField(queryset=Sentence.objects.all(), required=False, help_text="Hold Ctrl to select multiple.")

    class Meta(LearningItemForm.Meta):
        abstract = False
        model = Sentence
        fields = LearningItemForm.Meta.fields + ["response_to"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["response_to"].queryset = self.fields["response_to"].queryset.exclude(id=self.instance.id)
            self.fields["responses"].queryset = self.fields["response_to"].queryset



class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class ImportForm(forms.Form):
    words_csv = forms.FileField(required=False, label="CSV of words and sentences")
    audio_files = MultipleFileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(Div(Div("words_csv", css_class="col-12 col-md-8 col-lg-9"), Div(HTML(f"""<a href='{reverse_lazy("words_export")}' class='btn btn-info w-100'>Export existing words</a>"""), css_class="col-12 col-md-4 col-lg-3 mb-3"), css_class="row align-items-end"), "audio_files")
        self.helper.add_input(Submit('submit', "Upload", css_class="btn-secondary"))

    def clean(self):
        super().clean()
        if not self.cleaned_data["words_csv"] and not self.cleaned_data["audio_files"]:
            raise forms.ValidationError("Please upload a file.")
        