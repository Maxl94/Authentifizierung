from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from .models import Profile, Safezone
from .wsgi import CONTROLLER, ACTIVE_MODE
from .utilities.hw.nfc import NfcReader

def nfc_callback(status, id):
    if status == 1:
        global ACTIVE_MODE, CONTROLLER

        if ACTIVE_MODE == 1:
            ACTIVE_MODE = 3
        else:
            ACTIVE_MODE = 1

        obj = Profile.objects.get(id=ACTIVE_MODE)
        CONTROLLER.update_config(obj)
        print('Active mode = {0}'.format(ACTIVE_MODE))



NFC_READER = NfcReader(nfc_callback)
NFC_READER.start()


@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modes'] = Profile.objects.all().order_by('id')
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
        context['modes'] = Profile.objects.filter(id__gte=4)
        print(context['modes'])
        return context

@method_decorator(login_required, name='dispatch')
class CreateModeView(CreateView):
    model = Profile
    success_url = '/settings'
    template_name = 'create_mode.html'
    fields = '__all__'

@method_decorator(login_required, name='dispatch')
class UpdateModeView(UpdateView):
    model = Profile
    success_url = '/settings'
    template_name = 'update_mode.html'
    fields = '__all__'
    
    def get_object(self, queryset=None):
        obj = Profile.objects.get(id=self.kwargs['id'])
        return obj

@method_decorator(login_required, name='dispatch')
class DeleteModeView(DeleteView):
    model = Profile
    success_url = '/settings'
    template_name = 'delete_mode.html'

    def get_object(self, queryset=None):
        obj = Profile.objects.get(id=self.kwargs['id'])
        return obj

@method_decorator(login_required, name='dispatch')
class SetModeView(View):
    def get(self, request, **kwargs):
        obj = Profile.objects.get(id=self.kwargs['id'])
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

@method_decorator(login_required, name='dispatch')
class LocationsView(TemplateView):
    template_name = 'locations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['locations'] = Safezone.objects.filter(id__gte=2)
        print(context['locations'])
        return context

@method_decorator(login_required, name='dispatch')
class LocationCreateView(CreateView):
    template_name = 'locations_create.html'
    model = Safezone
    success_url = '/locations'
    fields = '__all__'

@method_decorator(login_required, name='dispatch')
class LocationUpdateView(UpdateView):
    model = Safezone
    success_url = '/locations'
    template_name = 'locations_update.html'
    fields = '__all__'
    
    def get_object(self, queryset=None):
        obj = Safezone.objects.get(id=self.kwargs['id'])
        return obj

@method_decorator(login_required, name='dispatch')
class LocationDeleteView(DeleteView):
    model = Safezone
    success_url = '/locations'
    template_name = 'locations_delete.html'
    
    def get_object(self, queryset=None):
        obj = Safezone.objects.get(id=self.kwargs['id'])
        return obj