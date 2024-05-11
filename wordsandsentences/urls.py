from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path('', login_required(views.IndexView.as_view(), login_url="/login/"), name='index'),
    path('word_audio/<int:pk>', login_required(views.WordAudioView.as_view(), login_url="/login/"), name='word_audio'),
    path('edit_list/', login_required(views.EditListView.as_view(), login_url="/login/"), name='edit_list'),
    path('topic_create/', login_required(views.TopicCreateView.as_view(), login_url="/login/"), name='topic_create'),
    path('topic_update/<int:pk>/', login_required(views.TopicUpdateView.as_view(), login_url="/login/"), name='topic_update'),
    path('topic_delete/<int:pk>/', login_required(views.TopicDeleteView.as_view(), login_url="/login/"), name='topic_delete'),
    path('word_create/<int:topic_pk>/', login_required(views.WordCreateView.as_view(), login_url="/login/"), name='word_create'),
    path('word_update/<int:pk>/', login_required(views.WordUpdateView.as_view(), login_url="/login/"), name='word_update'),
    path('word_delete/<int:pk>/', login_required(views.WordDeleteView.as_view(), login_url="/login/"), name='word_delete'),
    path('sentence_create/<int:topic_pk>/', login_required(views.SentenceCreateView.as_view(), login_url="/login/"), name='sentence_create'),
    path('sentence_update/<int:pk>/', login_required(views.SentenceUpdateView.as_view(), login_url="/login/"), name='sentence_update'),
    path('sentence_delete/<int:pk>/', login_required(views.SentenceDeleteView.as_view(), login_url="/login/"), name='sentence_delete'),
    path('import/', login_required(views.ImportView.as_view(), login_url="/login/"), name='import'),
    path('words_export/', login_required(views.WordsExportView.as_view(), login_url="/login/"), name='words_export'),
]
