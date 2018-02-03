"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from .views import *

urlpatterns = [
    url(r'^$', LoginView.as_view()),    
    url(r'^admin/', admin.site.urls),
    url(r'api/', include('server.api.urls'))
    url(r'^home/$', HomeView.as_view()),
    url(r'login/$', LoginView.as_view()),
    url(r'settings/$', SettingsView.as_view()),
    url(r'ir_sensor/$', VideoView.as_view()),
    url(r'settings/create/$', CreateModeView.as_view()),
    url(r'settings/update/(?P<id>\d+)/$', UpdateModeView.as_view()),
    url(r'settings/delete/(?P<id>\d+)/$', DeleteModeView.as_view()),
    url(r'set_mode/(?P<id>\d+)/$', SetModeView.as_view()),
    url(r'alarm_off/$', AlarmOffView.as_view()),
    url(r'locations/$', LocationsView.as_view()),
    url(r'locations/create/$', LocationCreateView.as_view()),
    url(r'locations/update/(?P<id>\d+)/$', LocationUpdateView.as_view()),
    url(r'locations/delete/(?P<id>\d+)/$', LocationDeleteView.as_view()),
]

