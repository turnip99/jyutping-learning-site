from django import forms
from django.contrib.auth import forms as auth_forms
from crispy_forms.helper import FormHelper


class FormWithHelperMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)


class LoginForm(FormWithHelperMixin, auth_forms.AuthenticationForm):
    pass