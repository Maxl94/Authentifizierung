from django.conf.urls import url, include
from django.contrib import admin
from .views import location

urlpatterns = [
    url(r'location$', location),
    url(r'ir_stream$', ir_stream),
]