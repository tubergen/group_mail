from django.core.urlresolvers import reverse
from django.utils.http import base36_to_int
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.views import create_group, join_group
from group_mail.apps.group.forms import CreateOrJoinGroupForm
from group_mail.apps.common.forms import AddEmailForm, ClaimEmailForm
from group_mail.apps.common.tokens import claim_email_token_generator


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
    errors = []
    form = AddEmailForm(request.user)
    if request.method == 'POST':
        if request.POST.get('add_email_submit'):
            form = AddEmailForm(request.user, request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                request.user.populate(email=email)
                return HttpResponseRedirect(reverse(email_added,
                    kwargs={'email': email}))
        elif request.POST.get('remove_email_submit'):
            email = request.POST.get('remove_email_submit')
            if len(request.user.email_set.all()) > 1:
                request.user.remove_email(email, unsubscribe=True)
                return HttpResponseRedirect(reverse(email_removed,
                    kwargs={'email': email}))
            else:
                errors.append('You cannot remove the only email associated with your account.'
                    'You must have one email at all times in order to log in.')

    return render_to_response('logged_in_homepage.html',
            {'groups_by_email': groups_by_email,
            'form': form,
            'errors': errors},
            context_instance=RequestContext(request))


def email_action(request, email, success_msg, action_type, validlink=True, new_user=None):
    if new_user:
        from django.contrib.auth.tokens import default_token_generator
        token = default_token_generator.make_token(new_user)
        uidb36 = int_to_base36(new_user.id)
    return render_to_response('common/email_action.html',
            {'validlink': validlink,
            'success_msg': success_msg,
            'action_type': action_type,
            'token': token},
            'uidb36': uidb36},
            context_instance=RequestContext(request))


def email_claim(request, email, validlink, new_user):
    success_msg = 'Successfully claimed %s, which now belongs to your account.' % email
    return email_action(request, email, success_msg, "claim", validlink, new_user)


def email_added(request, email):
    success_msg = 'Successfully added %s to your account.' % email
    return email_action(request, email, success_msg, "added")


def email_removed(request, email):
    success_msg = 'Successfully removed %s from your account.' % email
    return email_action(request, email, success_msg, "removed")


def claim_email(request, email):
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None

    if user and user.has_email(email):
        # there's no need to claim the email, so redirect
        return HttpResponseRedirect(reverse(homepage_splitter))

    if request.method == 'POST':
        form = ClaimEmailForm(user, request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            form.save(claim_user=user)
            return HttpResponseRedirect(reverse(claim_email_sent,
                kwargs={'email': email}))
    else:
        form = ClaimEmailForm(request.user)
    return render_to_response('common/claim_email_form.html',
            {'email': email,
            'form': form},
            context_instance=RequestContext(request))


def claim_email_sent(request, email):
    return render_to_response('common/claim_email_sent.html',
            {'email': email},
            context_instance=RequestContext(request))


def claim_email_confirm(request, uidb36=None, token=None, email=None):
    """
    Checks the hash in a claim email link and adds the email to the requested
    account if the link is valid.
    """
    assert uidb36 is not None and token is not None and email is not None  # checked by URLconf
    claim_user, valid_uid = _get_user_from_uid(uidb36)
    validlink = False
    new_user = None
    if valid_uid and claim_email_token_generator.check_token(email, token):
        # get the user associated with the claimed_email and remove that email
        # from the user's account
        old_user = CustomUser.objects.get(email=email)
        old_user.remove_email(email)

        # add the email to the claim_user's account
        new_user = _add_email_to_claim_user(email, claim_user)

        # post_reset_redirect = reverse('django.contrib.auth.views.password_reset_complete')
        validlink = True

    return email_claim(request, email, validlink, new_user)


def _get_user_from_uid(uidb36):
    """
    Return a tuple (user, valid_uid), where user is the user given by the uid
    (possibly None) and valid_uid tells us whether the uid is valid.

    A uid is invalid if it is nonzero and no user exists with that uid.
    """
    valid_uid = True
    uid_int = base36_to_int(uidb36)
    if uid_int == 0:
        claim_user = None
    else:
        try:
            claim_user = CustomUser.objects.get(id=uid_int)
        except (ValueError, CustomUser.DoesNotExist):
            valid_uid = False
    return claim_user, valid_uid


def _add_email_to_claim_user(email, claim_user):
    """
    Adds email to claim_user. If we create a new account for the user because
    claim_user is None, return the new user. Else, return None.
    """
    if claim_user:
        claim_user.populate(email)
        return None
    else:
        # need to create a new account for the user
        return CustomUser.objects.create_user(email=email)
