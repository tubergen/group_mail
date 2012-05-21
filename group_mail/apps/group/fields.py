import sys
import re
from django import forms
from django.core.validators import validate_email

email_separator_re = re.compile(r'[^\w\.\-\+@_]+')


class MultiEmailField(forms.Field):
    def to_python(self, value):
        "Normalize data to a list of strings."

        # Return an empty list if no input was given.
        if not value:
            return []
        return email_separator_re.split(value.strip())

    def validate(self, value):
        "Check if value consists only of valid emails."

        # Use the parent's handling of required fields, etc.
        super(MultiEmailField, self).validate(value)

        for email in value:
            try:
                validate_email(email)
            except forms.ValidationError:
                msg = 'The email %s appears to be invalid.' % email
                err_type, value, traceback = sys.exc_info()
                raise forms.ValidationError, (msg, err_type, value), traceback
