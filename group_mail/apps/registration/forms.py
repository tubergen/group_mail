from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import SetPasswordForm, AuthenticationForm
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


class UserEmailForm(forms.Form):
    email = forms.EmailField(max_length=CustomUser.MAX_LEN)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            if user.email == email:
                raise CustomUser.DuplicatePrimaryEmail(email=email, include_link=True)
            else:
                raise CustomUser.DuplicateEmail(email=email, include_link=True)
        except CustomUser.DoesNotExist:
            return email


class CreateUserForm(UserInfoForm, UserEmailForm):
    """
    # remove password field for now
    password = forms.CharField(max_length=CustomUser.MAX_LEN,
            widget=forms.PasswordInput)
    """

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
        fields = ['first_name', 'last_name', 'phone_number']
        for field in fields:
            self._add_initial(kwargs, user, field)
        super(CompleteAccountForm, self).__init__(user, *args, **kwargs)

    def save(self, commit=True):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.phone_number = self.cleaned_data['phone_number']
        # call SetPasswordForm's save(), which calls save() on the user
        return super(CompleteAccountForm, self).save(commit)

    def _add_initial(self, kwargs, user, field):
        """
        Adds user.field to kwarg's initial dictionary if user.field is
        not None.
        """
        value = eval('user.%s' % field)
        if value:
            kwargs['initial'][field] = value


class LoginForm(AuthenticationForm):
    def clean(self):
        """
        This is identical to the default implementation of AuthenticationForm,
        except that we have special logic to get the username.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        username = CustomUser.objects.get_real_username(username)

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'])
            elif not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
        self.check_for_test_cookie()
        return self.cleaned_data
