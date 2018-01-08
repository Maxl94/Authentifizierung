from django.http import HttpResponseRedirect
from django.views.generic import View, TemplateView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator



class HomeView(TemplateView):
    template_name = 'home.html'