from django import forms
# from django.contrib.auth.forms import PasswordResetForm
from group_mail.apps.common.models import CustomUser
from group_mail.apps.registration.forms import UserEmailForm


class AddEmailForm(UserEmailForm):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN,
            label="Do you have an email that doesn't appear below?  Add it here:",
            widget=forms.TextInput(attrs={
                'class': 'input-small',
                'label': 'hi',
                'placeholder': 'e.g.: brian@gmail.com'}))

    def __init__(self, claim_user, *args, **kwargs):
        super(UserEmailForm, self).__init__(*args, **kwargs)
        self.claim_user = claim_user

    def clean_email(self):
        try:
            return super(AddEmailForm, self).clean_email()
        except CustomUser.DuplicateEmail:
            email = self.cleaned_data['email']
            if self.claim_user.has_email(email):
                raise CustomUser.DuplicateEmail(
                        msg='The email already belongs to your account.')
            else:
                raise CustomUser.DuplicateEmail(email=email, include_claim_link=True)


class ClaimEmailForm(forms.Form):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN)

    def __init__(self, claim_user, *args, **kwargs):
        super(ClaimEmailForm, self).__init__(*args, **kwargs)
        self.claim_user = claim_user

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.claim_user.has_email(email):
            raise CustomUser.DuplicateEmail(msg='The email already belongs to your account.')
        return email

    def save(self,
             subject_template_name='common/claim_email_subject.txt',
             email_template_name='common/claim_email_email.html',
             from_email=None,
             claim_user=None,
             request=None):
        """
        Generates a one-use only link for claiming an email and sends it to the
        email.
        """
        from django.contrib.auth.tokens import default_token_generator
        from django.contrib.sites.models import get_current_site
        from django.template import loader
        from django.utils.http import int_to_base36
        from django.core.mail import send_mail

        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain
        claim_email_addr = self.cleaned_data['email']
        # below, we use claim_user to generate the uid and token.
        # this is because, if the 'claim request' is successful, claim_user
        # is the account to which we'll add the email
        c = {
            'email': claim_email_addr,
            'domain': domain,
            'site_name': site_name,
            'uid': int_to_base36(claim_user.id),
            'claim_user': claim_user,
            'token': default_token_generator.make_token(claim_user),
            'protocol': 'http',
        }
        subject = loader.render_to_string(subject_template_name, c)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        email = loader.render_to_string(email_template_name, c)
        send_mail(subject, email, from_email, [claim_email_addr])
