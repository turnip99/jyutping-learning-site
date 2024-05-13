from django import forms
from django.contrib.auth import forms as auth_forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class FormWithHelperMixin:
    submit_text = "Save"
    submit_css_class = "btn-secondary"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit('submit', self.submit_text, css_class=self.submit_css_class))


class LoginForm(FormWithHelperMixin, auth_forms.AuthenticationForm):
    submit_text = "Log in"