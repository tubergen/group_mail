from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.template import RequestContext
from eventboard.apps.events.forms import EventCreationForm
from eventboard.apps.events.models import Event
from datetime import datetime


def create_group(request):
    if request.method == 'POST':
        form = EventCreationForm(request.POST)
        if form.is_valid():
            """ create a group in mailman and on server """
            """ if email is new, create a new user """
            """ change behavior slightly if user is logged in """
            """ the below code is garbage """
            e = Event()
            e.title = form.cleaned_data['title']
            e.description = form.cleaned_data['description']
            e.location = form.cleaned_data['location']
            e.date = datetime.combine(form.cleaned_data['date'],
                                      form.cleaned_data['time'])
            if False:  # temporary until we have accounts
                e.user = request.user
            else:
                u = User(username=e.title)
                u.save()
                e.creator = u
            e.save()
            return HttpResponseRedirect('/submit/thanks/')
    else:
        form = EventCreationForm()

    return render_to_response('group/create.html',
                              {'form': form},
                              RequestContext(request))
