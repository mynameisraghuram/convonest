from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def csrf(request):
    # Sets csrftoken cookie on the response
    return JsonResponse({"detail": "CSRF cookie set"})
