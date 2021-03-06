from django import forms
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
        group_name = self.cleaned_data['group_name']
        group_code = self.cleaned_data['group_code']
        try:
            Group.objects.validate_group_code(group_code)
            Group.objects.validate_group_uniqueness(group_name, group_code)
        except forms.ValidationError:
            raise
        return group_code


class JoinGroupForm(GroupForm, PopulatedEmailForm):
    def clean_group_name(self):
        group_name = self.cleaned_data['group_name']
        self.groups = Group.objects.filter(name=group_name)
        if len(self.groups) == 0:
            raise forms.ValidationError('The group %s does not exist.' % group_name)
        return group_name

    def clean_group_code(self):
        group_code = self.cleaned_data['group_code']
        if self.groups:
            for group in self.groups:
                if group.code == group_code:
                    return group_code
            # we didn't find a single group with this group code
            raise Group.CodeInvalid(name=self.group.name, code=group_code)
        else:
            # we'll focus the user on the 'no group with that name' error by
            # returning cleanly here
            return group_code


class CreateOrJoinGroupForm(GroupForm, UserEmailForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            CustomUser.objects.get(email=email)
            e = CustomUser.DuplicateEmail(email=email)
            e.messages[0] += ' Please log in if that account belongs to you.'
            raise e
        except CustomUser.DoesNotExist:
            return email


class GroupNavbarForm(CreateGroupForm):
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
