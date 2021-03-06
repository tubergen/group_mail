from django import forms
from group_mail.apps.common.models import CustomUser
from group_mail.apps.registration.forms import UserEmailForm

# CustomPasswordResetForm lives in custom_user_manager.py


class ClaimEmailForm(forms.Form):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN,
            label="Do you have an email that doesn't appear below?  Add it here:",
            widget=forms.TextInput(attrs={
                'class': 'input-small',
                'placeholder': 'e.g.: brian@gmail.com'}))

    def __init__(self, claim_user, *args, **kwargs):
        super(ClaimEmailForm, self).__init__(*args, **kwargs)
        self.claim_user = claim_user

    def clean_email(self):
        email = self.cleaned_data['email']
        # The call to has_email() below relies on an email obj existing, as
        # does much of our claim code elsewhere.
        self._create_email_object(email)
        if self.claim_user and self.claim_user.has_email(email):
            raise CustomUser.DuplicateEmail(msg='The email already belongs to your account.')
        return email

    def _create_email_object(self, email):
        """
        Creates an Email object for the email if one doesn't already exist
        by creating an incomplete user with that email.

        Since the user is going to get a claim-email-confirm email, we don't
        send him a welcome email.
        """
        CustomUser.objects.get_or_create_user(email=email, send_welcome=False)

    def save(self,
             subject_template_name='common/claim_email_subject.txt',
             email_template_name='common/claim_email_email.html',
             from_email=None,
             claim_user=None,
             request=None):
        """
        Generates a one-use only link for claiming an email and sends it to the
        email.

        We use the claiming user to generate the uid, since if the claim_request
        is successful, that's the account to which we'll add the email.
        """
        from django.contrib.sites.models import get_current_site
        from django.template import loader
        from django.utils.http import int_to_base36
        from django.core.mail import send_mail
        from group_mail.apps.common.tokens import claim_email_token_generator

        current_site = get_current_site(request)
        claim_email_addr = self.cleaned_data['email']
        uid = claim_user.id if claim_user else 0
        c = {
            'email': claim_email_addr,
            'domain': current_site.domain,
            'site_name': current_site.name,
            'uid': int_to_base36(uid),
            'claim_user': claim_user,
            'token': claim_email_token_generator.make_token(claim_email_addr),
            'protocol': 'http',
        }
        subject = loader.render_to_string(subject_template_name, c)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        email = loader.render_to_string(email_template_name, c)
        send_mail(subject, email, from_email, [claim_email_addr])
