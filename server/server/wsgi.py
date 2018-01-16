"""
WSGI config for server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from .utilities.control import Control
from .models import Setting

ACTIVE_MODE = 1
setting = Setting.objects.get(id=ACTIVE_MODE)
CONTROLLER = Control(setting)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

application = get_wsgi_application()
