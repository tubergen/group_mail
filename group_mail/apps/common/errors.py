from django.forms import ValidationError


class CustomException(ValidationError):
    """
    Override the default way python prints errors as strings.
    """
    def __init__(self, msg=None):
        self.msg = msg
        super(CustomException, self).__init__(msg)

    def __str__(self):
        return self.msg
