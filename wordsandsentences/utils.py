from django.db.models import Q

from .models import Topic


def get_topic_dict(exclude_empty_topics=False):
    topic_dict = {}
    topics = Topic.objects.all()
    if exclude_empty_topics:
        topics = topics.filter(Q(word__isnull=False) | Q(sentence__isnull=False)).distinct()
    for topic in topics:
        topic_dict[topic] = {"words": topic.word_set.all(), "sentences": topic.sentence_set.all()}
    return topic_dict
