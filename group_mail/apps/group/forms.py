from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import PasswordResetForm
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.models import Group
from group_mail.apps.group.fields import MultiEmailField
from group_mail.apps.registration.forms import UserEmailForm


class GroupForm(forms.Form):
    group_name = forms.CharField(max_length=Group.MAX_LEN)
    group_code = forms.CharField(max_length=Group.MAX_LEN)


class PopulatedEmailForm(forms.Form):
    email = forms.ChoiceField(choices=[])

    def __init__(self, user, *args, **kwargs):
        super(PopulatedEmailForm, self).__init__(*args, **kwargs)
        self.fields['email'].choices = \
                [(email_obj.email, email_obj.email) for email_obj in user.email_set.all()]


class CreateGroupForm(GroupForm, PopulatedEmailForm):
    def clean_group_name(self):
        group_name = self.cleaned_data['group_name']
        try:
            Group.objects.validate_group_name(group_name)
        except forms.ValidationError:
            raise
        return group_name

    def clean_group_code(self):
        group_code = self.cleaned_data['group_code']
        try:
            Group.objects.validate_group_code(group_code)
        except forms.ValidationError:
            raise
        return group_code


class JoinGroupForm(GroupForm, PopulatedEmailForm):
    def clean_group_name(self):
        group_name = self.cleaned_data['group_name']
        try:
            self.group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            raise forms.ValidationError('The group %s does not exist.' % group_name)
        return group_name

    def clean_group_code(self):
        group_code = self.cleaned_data['group_code']
        if self.group:
            if self.group.code != group_code:
                raise Group.CodeInvalid(name=self.group.name, code=group_code)
        return group_code


class CreateOrJoinGroupForm(GroupForm, UserEmailForm):
    def clean_email(self):
        try:
            return super(CreateOrJoinGroupForm, self).clean_email()
        except CustomUser.DuplicateEmail as e:
            e.messages[0] += ' Please log in if that account belongs to you.'
            raise


class CreateGroupNavbarForm(CreateGroupForm):
    group_name = forms.CharField(max_length=Group.MAX_LEN,
            widget=forms.TextInput(attrs={
                'class': 'input-medium',
                'placeholder': 'Group name'}))
    group_code = forms.CharField(max_length=Group.MAX_LEN,
            widget=forms.TextInput(attrs={
                'class': 'input-small',
                'placeholder': 'Group code'}))


class AddMembersForm(forms.Form):
    emails = MultiEmailField(
            error_messages={'required': "You didn't enter any emails."},
            widget=forms.Textarea(attrs={
                'class': 'input-xlarge',
                'rows': '3',
                'placeholder': 'brian@gmail.com, anne@gmail.com, ellie@gmail.com'})
            )


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
        return '<a href="email/claim/%s">here</a>' % email


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
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'claim_user': claim_user,
                'token': default_token_generator.make_token(user),
                'protocol': 'http',
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            send_mail(subject, email, from_email, [user.email])
