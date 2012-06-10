from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import PasswordResetForm
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.forms import UserEmailForm


class AddEmailForm(UserEmailForm):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN,
            label="Do you have an email that doesn't appear below?  Add it here:",
            widget=forms.TextInput(attrs={
                'class': 'input-small',
                'label': 'hi',
                'placeholder': 'e.g.: brian@gmail.com'}))

    def clean_email(self):
        try:
            return super(AddEmailForm, self).clean_email()
        except CustomUser.DuplicateEmail:
            email = self.cleaned_data['email']
            raise CustomUser.DuplicateEmail(
                    msg=mark_safe('The email already belongs to an account.'
                    ' Please click %s' % self.claim_email_link_html(email) + \
                    ' if the email belongs to you.'),
                    email=email)

    def claim_email_link_html(self, email):
        return '<a href="claim/email/%s">here</a>' % email


class ClaimEmailForm(PasswordResetForm):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN)

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

        # PasswordResetForm populates users_cache in clean_email()
        for user in self.users_cache:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
            # below, we use claim_user to generate the uid and token.
            # this is because, if the 'claim request' is successful, claim_user
            # is the account to which we'll add the email
            c = {
                'email': user.email,
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
            send_mail(subject, email, from_email, [user.email])
