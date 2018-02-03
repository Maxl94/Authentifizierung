import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from server.models import Safezone

@login_required
def location(request):
    safe_zone = Safezone.objects.get(id=1)
    res = {
        'latitude': safe_zone.latitude,
        'longitude': safe_zone.longitude,
    }
    return JsonResponse(res)