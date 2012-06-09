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
        return '<a href="claim/email/%s">here</a>' % email


class ClaimEmailForm(PasswordResetForm):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN)
