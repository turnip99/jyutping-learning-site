from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Div
from django.urls import reverse_lazy


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
        self.helper.layout = Layout(Div(Div("words_csv", css_class="col"), Div(HTML(f"<a href='{reverse_lazy("words_export")}' class='btn btn-info'>Export existing words</a>"), css_class="col-auto mb-3"), css_class="row align-items-end"), "audio_files")

    def clean(self):
        super().clean()
        if not self.cleaned_data["words_csv"] and not self.cleaned_data["audio_files"]:
            raise forms.ValidationError("Please upload a file.")
        