from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic

from .forms import LoginForm


class LoginView(generic.FormView):
    template_name = "login.html"
    form_class = LoginForm

    def form_valid(self, form):
        if user := authenticate(self.request, username=form.cleaned_data["username"], password=form.cleaned_data["password"]):
            login(self.request, user)
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.request.GET.get("next", reverse_lazy("index"))


class LogoutView(generic.View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')
