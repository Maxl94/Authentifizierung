import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from server.models import Safezone
from server.wsgi import CONTROLLER

@login_required
def location(request):
    safe_zone = Safezone.objects.get(id=1)
    res = {
        'latitude': safe_zone.latitude,
        'longitude': safe_zone.longitude,
    }
    return JsonResponse(res)


@login_required
def ir_stream(request):
    return StreamingHttpResponse(gen(),content_type="image/jpeg")

def gen():
    while True:
        frame = CONTROLLER.motion.get_frame()
        yield(frame)
