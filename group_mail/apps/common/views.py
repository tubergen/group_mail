from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.views import create_group, join_group
from group_mail.apps.group.forms import CreateOrJoinGroupForm


def homepage_splitter(request):
    if request.user.is_authenticated():
        return logged_in_homepage(request)
    else:
        return landing_page(request)


def landing_page(request):
    if request.method == 'POST' and 'submit' in request.POST:
        form = CreateOrJoinGroupForm(request.POST)
        if form.is_valid():
            user = CustomUser.objects.create_user(email=form.cleaned_data['email'])
            auth_user = authenticate(username=user.email, password=None)
            login(request, auth_user)
            """
            Now that we've created the user from the email, we pass off the rest
            of the validation to the dedicated create / join group functions.
            """
            if request.POST['submit'] == 'Create':
                return create_group(request)
            elif request.POST['submit'] == 'Join':
                return join_group(request)
    else:
        form = CreateOrJoinGroupForm()

    return render_to_response('landing.html',
                              {'form': form,
                               'type_create': 'Create',
                               'type_join': 'Join'},
                              RequestContext(request))


@login_required
def logged_in_homepage(request):
    groups_by_email = request.user.get_groups_by_email()
    return render_to_response('group/list.html',
            {'groups_by_email': groups_by_email},
            context_instance=RequestContext(request))
