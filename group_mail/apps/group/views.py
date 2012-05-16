from django.shortcuts import render_to_response
from django.template import RequestContext
from group_mail.apps.common.models import Group, CustomUser


def group_info(request, group_name):
    group = Group.objects.get(name=group_name)
    errors = []
    if request.method == 'POST':
        if not request.POST.get('removed_members'):
            errors.append('No members were selected to be removed.')
        if not errors:
            for member_email in request.POST['removed_members']:
                user = CustomUser.objects.get(member_email)
                group.members.remove(user)

    return render_to_response('group/info.html',
            {'group': group,
            'errors': errors},
            context_instance=RequestContext(request))


'''
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
'''
