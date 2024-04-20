from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('wordsandsentences.urls')),
    path('admin/', admin.site.urls),
]
