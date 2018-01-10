from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from .models import Setting




class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modes'] = Setting.objects.all().order_by('id')
        print(context['modes'])
        return context

class LoginView(View):
    def get(self, request):
        context = {}
        return render(request, 'login.html', context)

    def post(self, request):
        username = 'locados'
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/home')
        else:
            context = {
                'error':'Pin is not correct',
            }
            return render(request, 'login.html', context)

class SettingsView(TemplateView):
    template_name = 'settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modes'] = Setting.objects.filter(id__gte=4)
        print(context['modes'])
        return context


class CreateModeView(CreateView):
    model = Setting
    success_url = '/settings'
    template_name = 'create_mode.html'
    fields = '__all__'


class UpdateModeView(UpdateView):
    model = Setting
    success_url = '/settings'
    template_name = 'update_mode.html'
    fields = '__all__'
    
    def get_object(self, queryset=None):
        obj = Setting.objects.get(id=self.kwargs['id'])
        return obj


class DeleteModeView(DeleteView):
    model = Setting
    success_url = '/settings'
    template_name = 'delete_mode.html'

    def get_object(self, queryset=None):
        obj = Setting.objects.get(id=self.kwargs['id'])
        return obj
