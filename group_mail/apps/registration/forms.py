from django import forms
from django.contrib.auth.forms import SetPasswordForm
from group_mail.apps.common.models import CustomUser

name_invalid = "This value may contain only letters, numbers, hyphens, apostrophes, and periods."
phone_number_help = 'We need this so that you can join groups with text messages.'


class CreateUserForm(forms.Form):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN)
    """
    # remove password field for now
    password = forms.CharField(max_length=CustomUser.MAX_LEN,
            widget=forms.PasswordInput)
    """
    first_name = forms.RegexField(max_length=30, regex=r"^[\w.'-]+$",
        error_messages={'invalid': name_invalid})
    last_name = forms.RegexField(max_length=30, regex=r"^[\w.'-]+$",
        error_messages={'invalid': name_invalid})
    phone_number = forms.RegexField(max_length=30, regex=r"^[\d.'-]+$",
        help_text=phone_number_help,
        error_messages={'invalid': 'This field may only contain numbers.',
            'required': 'This field is required. %s' % phone_number_help})

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            CustomUser.objects.get(email=email)
            raise forms.ValidationError('A user with that email already exists.')
        except CustomUser.DoesNotExist:
            return email


class CompleteAccountForm(SetPasswordForm, CreateUserForm):
    def __save__(self, commit=True):
        # call SetPasswordForm's save()
        user = super(CompleteAccountForm, self).__save__(commit)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.save()
        return user
