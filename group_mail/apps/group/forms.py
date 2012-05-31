from django import forms
from group_mail.apps.group.models import Group
from group_mail.apps.group.fields import MultiEmailField


class GroupForm(forms.Form):
    group_name = forms.CharField(max_length=Group.MAX_LEN)
    group_code = forms.CharField(max_length=Group.MAX_LEN)


class CreateGroupForm(GroupForm):
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


class JoinGroupForm(GroupForm):
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
