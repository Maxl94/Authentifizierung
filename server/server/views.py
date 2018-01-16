from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from .models import Setting
from .wsgi import CONTROLLER



@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modes'] = Setting.objects.all().order_by('id')
        context['active_mode'] = ACTIVE_MODE
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

@method_decorator(login_required, name='dispatch')
class SettingsView(TemplateView):
    template_name = 'settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modes'] = Setting.objects.filter(id__gte=4)
        print(context['modes'])
        return context

@method_decorator(login_required, name='dispatch')
class CreateModeView(CreateView):
    model = Setting
    success_url = '/settings'
    template_name = 'create_mode.html'
    fields = '__all__'

@method_decorator(login_required, name='dispatch')
class UpdateModeView(UpdateView):
    model = Setting
    success_url = '/settings'
    template_name = 'update_mode.html'
    fields = '__all__'
    
    def get_object(self, queryset=None):
        obj = Setting.objects.get(id=self.kwargs['id'])
        return obj

@method_decorator(login_required, name='dispatch')
class DeleteModeView(DeleteView):
    model = Setting
    success_url = '/settings'
    template_name = 'delete_mode.html'

    def get_object(self, queryset=None):
        obj = Setting.objects.get(id=self.kwargs['id'])
        return obj

@method_decorator(login_required, name='dispatch')
class SetModeView(View):
    def get(self, request, **kwargs):
        obj = Setting.objects.get(id=self.kwargs['id'])
        # Rufe Michis Zeug auf
        
        print('Michis zeug aufrufen')
        global ACTIVE_MODE, CONTROLLER
        ACTIVE_MODE = obj.id
        CONTROLLER.update_config(obj)
        print('Active mode = {0}'.format(ACTIVE_MODE))
        return redirect('/home')

@method_decorator(login_required, name='dispatch')
class AlarmOffView(View):
    def get(self, request):
        print('Alarm aus')
        global CONTROLLER
        CONTROLLER.stop_alarm()
        return redirect('/home')

@method_decorator(login_required, name='dispatch')
class VideoView(TemplateView):
    template_name = "ir_sensor.html"