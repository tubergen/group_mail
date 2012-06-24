"""
The following code is a copy/paste from:
https://github.com/django/django/blob/master/django/contrib/auth/views.py

I had to change the line marked (***changed***).
"""
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.utils.http import base36_to_int
from django.template.response import TemplateResponse
from group_mail.apps.common.models import CustomUser
from group_mail.apps.registration.forms import CompleteAccountForm


# Doesn't need csrf_protect since no-one can guess the URL
@sensitive_post_parameters()
@never_cache
def password_reset_confirm(request, uidb36=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None,
                           current_app=None, extra_context=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    assert uidb36 is not None and token is not None  # checked by URLconf
    if post_reset_redirect is None:
        post_reset_redirect = reverse('django.contrib.auth.views.password_reset_complete')
    try:
        uid_int = base36_to_int(uidb36)
        user = CustomUser.objects.get(id=uid_int)  # (***changed***)
    except (ValueError, CustomUser.DoesNotExist):  # (***changed***)
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
            else:
                raise Exception(form.errors)
        else:
            form = set_password_form(user)  # (***changed***)
    else:
        validlink = False
        form = None
    context = {
        'form': form,
        'validlink': validlink,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


# Doesn't need csrf_protect since no-one can guess the URL
@sensitive_post_parameters()
@never_cache
def complete_account(request, email,
                    template_name='registration/complete_account.html'):
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = CompleteAccountForm(user, request.POST)
        if form.is_valid():
            form.save()
            redirect = reverse('django.contrib.auth.views.password_reset_complete')
            return HttpResponseRedirect(redirect)
        else:
            raise Exception(form.errors)
    else:
        form = CompleteAccountForm(user)
    context = {'form': form}
    return TemplateResponse(request, template_name, context)
