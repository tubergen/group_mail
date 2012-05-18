# from django.conf import settings
from django.contrib.auth.models import UserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordResetForm
# from group_mail.apps.mailman import mailman_cmds


class CustomUserManager(UserManager):
    def send_welcome_email(request, to_email):
        try:
            validate_email(to_email)
        except ValidationError:
            raise

        # use the password reset form to send the welcome email to easily
        # obtain password reset url
        form = PasswordResetForm({'email': to_email})
        if form.is_valid():
            opts = {
                'email_template_name': 'registration/welcome_email.html',
                'subject_template_name': 'registration/welcome_subject.txt',
            }
            form.save(**opts)

    def create_user(self, email, password=None, first_name=None, \
            last_name=None, phone_number=None):
        # we do the import here to avoid a circular dependency
        from group_mail.apps.common.models import CustomUser

        # validate the phone number provided is unique to the new user
        try:
            user = CustomUser.objects.get(phone_number=phone_number)
            raise CustomUser.DuplicatePhoneNumber()
        except CustomUser.DoesNotExist:
            pass

        # validate the email
        try:
            validate_email(email)
        except ValidationError:
            raise

        # validate the email provided is unique to the new user
        try:
            CustomUser.objects.get(email=email)
            raise CustomUser.DuplicateEmail()
        except CustomUser.DoesNotExist:
            user = super(CustomUserManager, self).create_user(
                    username=email,
                    email=email,
                    password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.phone_number = phone_number
            user.save()

            self.send_welcome_email(email)
