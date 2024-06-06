from django.urls import path
from django.contrib.auth.decorators import login_required

from jyutpinglearningsite.decorators import staff_required
from . import views

urlpatterns = [
    path('', login_required(views.IndexView.as_view(), login_url="/login/"), name='index'),
    path('quiz/', login_required(views.QuizView.as_view(), login_url="/login/"), name='quiz'),
    path('flashcards/', login_required(views.FlashcardsView.as_view(), login_url="/login/"), name='flashcards'),
    path('edit_list/', staff_required(views.EditListView.as_view()), name='edit_list'),
    path('topic_create/', staff_required(views.TopicCreateView.as_view()), name='topic_create'),
    path('topic_update/<int:pk>/', staff_required(views.TopicUpdateView.as_view()), name='topic_update'),
    path('topic_delete/<int:pk>/', staff_required(views.TopicDeleteView.as_view()), name='topic_delete'),
    path('word_create/<int:topic_pk>/', staff_required(views.WordCreateView.as_view()), name='word_create'),
    path('word_update/<int:pk>/', staff_required(views.WordUpdateView.as_view()), name='word_update'),
    path('word_delete/<int:pk>/', staff_required(views.WordDeleteView.as_view()), name='word_delete'),
    path('sentence_create/<int:topic_pk>/', staff_required(views.SentenceCreateView.as_view()), name='sentence_create'),
    path('sentence_update/<int:pk>/', staff_required(views.SentenceUpdateView.as_view()), name='sentence_update'),
    path('sentence_delete/<int:pk>/', staff_required(views.SentenceDeleteView.as_view()), name='sentence_delete'),
    path('import/', staff_required(views.ImportView.as_view()), name='import'),
    path('topics_export/', staff_required(views.TopicsExportView.as_view()), name='topics_export'),
    path('words_export/', staff_required(views.WordsExportView.as_view()), name='words_export'),
]
