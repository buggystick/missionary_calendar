from django.conf import settings


def ward_title(request):
    return {'ward_title': settings.WARD_TITLE}
