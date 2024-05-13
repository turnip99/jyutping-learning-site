from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from . import views
from .decorators import logged_out_required


urlpatterns = [
    path('', include('wordsandsentences.urls')),
    path('login/', logged_out_required(views.LoginView.as_view()), name='login'),
    path('logout/', login_required(views.LogoutView.as_view(), login_url="/login/"), name='logout'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)