from django.conf import settings

def get_debug(request):
    return {'debug': settings.DEBUG}
