from django import forms
from django.contrib.auth.forms import SetPasswordForm
from group_mail.apps.common.models import CustomUser

name_invalid = "This value may contain only letters, numbers, hyphens, apostrophes, and periods."
phone_number_help = 'We need this so that you can join groups with text messages.'


class UserInfoForm(forms.Form):
    first_name = forms.RegexField(max_length=30, regex=r"^[\w.'-]+$",
        error_messages={'invalid': name_invalid})
    last_name = forms.RegexField(max_length=30, regex=r"^[\w.'-]+$",
        error_messages={'invalid': name_invalid})
    phone_number = forms.RegexField(max_length=30, regex=r"^[\d.'-]+$",
        help_text=phone_number_help,
        error_messages={'invalid': 'This field may only contain numbers.',
            'required': 'This field is required. %s' % phone_number_help})


class CreateUserForm(UserInfoForm):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN)
    """
    # remove password field for now
    password = forms.CharField(max_length=CustomUser.MAX_LEN,
            widget=forms.PasswordInput)
    """
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            CustomUser.objects.get(email=email)
            raise forms.ValidationError('A user with that email already exists.')
        except CustomUser.DoesNotExist:
            return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        try:
            CustomUser.objects.get(phone_number=phone_number)
            raise CustomUser.DuplicatePhoneNumber(phone_number=phone_number)
        except CustomUser.DoesNotExist:
            return phone_number


class CompleteAccountForm(SetPasswordForm, UserInfoForm):
    def __init__(self, user, *args, **kwargs):
        kwargs['initial'] = {}
        kwargs['initial']['first_name'] = user.first_name
        kwargs['initial']['last_name'] = user.last_name
        kwargs['initial']['phone_number'] = user.phone_number
        super(CompleteAccountForm, self).__init__(user, *args, **kwargs)

    def __save__(self, commit=True):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.phone_number = self.cleaned_data['phone_number']
        # call SetPasswordForm's save()
        return super(CompleteAccountForm, self).__save__(commit)
