from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from group_mail.apps.registration.forms import CreateUserForm
from group_mail.apps.common.models import CustomUser
from django.views.generic import TemplateView


def register(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            CustomUser.objects.create_user(
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone_number=form.cleaned_data['phone_number'])
            return HttpResponseRedirect("/register/thanks/")
    else:
        form = CreateUserForm()

    return render_to_response("registration/register.html",
            {'form': form},
            context_instance=RequestContext(request))


def register_thanks(request):
    return TemplateView.as_view(template_name='registration/register_thanks.html')(request)
