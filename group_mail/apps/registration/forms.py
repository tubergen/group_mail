from django import forms
from group_mail.apps.common.models import CustomUser

name_invalid = "This value may contain only letters, numbers, hyphens, apostrophes, and periods."


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

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            CustomUser.objects.get(email=email)
            raise forms.ValidationError('A user with that email already exists.')
        except CustomUser.DoesNotExist:
            return email
