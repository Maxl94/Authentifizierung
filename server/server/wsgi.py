"""
WSGI config for server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from .utilities.control import Control
from .models import Profile, Safezone

ACTIVE_MODE = 1
setting = Profile.objects.get(id=ACTIVE_MODE)
safe_zones = Safezone.objects.get(id=1)
CONTROLLER = Control(setting, safe_zones, db_is_ready=True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

application = get_wsgi_application()
