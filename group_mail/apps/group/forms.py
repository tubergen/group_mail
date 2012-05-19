from django import forms
from group_mail.apps.common.models import Group


class CreateGroupForm(forms.Form):
    group_name = forms.CharField(max_length=Group.MAX_LEN)
    group_code = forms.CharField(max_length=Group.MAX_LEN)

    def clean_group_name(self):
        group_name = self.cleaned_data['group_name']
        try:
            Group.objects.validate_group_name(group_name)
        except Group.AlreadyExists:
            raise forms.ValidationError("Group with that name already exists.")
        except Group.NameTooLong:
            raise forms.ValidationError("Name must not exceed %d characters." % \
                    Group.MAX_LEN)
        return group_name

    def clean_group_code(self):
        group_code = self.cleaned_data['group_code']
        try:
            Group.objects.validate_group_code(group_code)
        except Group.NameTooLong:
            raise forms.ValidationError("Code must not exceed %d characters." % \
                    Group.MAX_LEN)
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
