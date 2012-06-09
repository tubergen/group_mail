from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse
from django.utils.http import base36_to_int
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.views import create_group, join_group
from group_mail.apps.group.forms import CreateOrJoinGroupForm, AddEmailForm, ClaimEmailForm


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
    if request.method == 'POST':
        form = AddEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            request.user.populate(email=email)
            return HttpResponseRedirect('email/added/%s' % email)
    else:
        form = AddEmailForm()

    return render_to_response('group/list.html',
            {'groups_by_email': groups_by_email,
            'form': form},
            context_instance=RequestContext(request))


@login_required
def email_added(request, email):
    return render_to_response('common/email_added.html',
            {'email': email},
            context_instance=RequestContext(request))


@login_required
def claim_email(request, email):
    if request.method == 'POST':
        form = ClaimEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            form.save(subject_template_name='common/claim_email_subject.txt',
                    email_template_name='common/claim_email_email.html')
            return render_to_response('common/claim_email_sent.html',
                    {'email': email},
                    context_instance=RequestContext(request))
    else:
        form = ClaimEmailForm()
    return render_to_response('common/claim_email_form.html',
            {'email': email,
            'form': form},
            context_instance=RequestContext(request))


@login_required
def claim_email_confirm(request, uidb36=None, token=None):
    """
    Checks the hash in a claim email link and adds the email to the requested account if the link is valid
    """
    assert uidb36 is not None and token is not None  # checked by URLconf
    post_reset_redirect = reverse('django.contrib.auth.views.password_reset_complete')
    try:
        uid_int = base36_to_int(uidb36)
        user = CustomUser.objects.get(id=uid_int)
    except (ValueError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        return HttpResponseRedirect(post_reset_redirect)
