from django.urls import reverse_lazy
from django.views import generic

from .forms import ImportForm


class IndexView(generic.TemplateView):
    template_name = "index.html"


class ImportExportView(generic.FormView):
    template_name = "import_export.html"
    form_class = ImportForm
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)