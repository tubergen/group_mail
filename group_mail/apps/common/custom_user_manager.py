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
        else:
            raise Exception(str(form.errors))

    def create_user(self, email, password=None, first_name=None, \
            last_name=None, phone_number=None):
        """ Creates a CustomUser with the values given by the parameters and returns
            the CustomUser if successful."""
        # we do the import here to avoid a circular dependency
        from group_mail.apps.common.models import CustomUser

        if phone_number:
            # validate the phone number provided is unique to the new user
            try:
                user = CustomUser.objects.get(phone_number=phone_number)
                raise CustomUser.DuplicatePhoneNumber(phone_number=phone_number)
            except CustomUser.DoesNotExist:
                pass

        # validate the email
        try:
            validate_email(email)
        except ValidationError:
            raise

        # validate the email provided is unique to the new user
        try:
            user = CustomUser.objects.get(email=email)
            if user.is_complete():
                raise CustomUser.DuplicateEmail(email=email)
            else:
                """ this user's account is incomplete, so we'll allow
                    this function to populate the user's account with
                    additional info """
                pass
        except CustomUser.DoesNotExist:
            user = super(CustomUserManager, self).create_user(
                    username=email,
                    email=email,
                    password='password')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if phone_number:
            user.phone_number = phone_number
        user.save()
        self.send_welcome_email(email)
        return user

    def get_or_create_user(self, email, password=None, first_name=None, \
            last_name=None, phone_number=None):
        """
        Get's the user with the specified email so long as the phone number
        matches that account. If the phone number doesn't match, raises
        an exception. Creates a user if the email doesn't exist. Returns
        the user.
        """
        # we do the import here to avoid a circular dependency
        from group_mail.apps.common.models import CustomUser

        try:
            user = CustomUser.objects.get(email=email)
            if user.phone_number and user.phone_number != phone_number:
                """ there exists a user, but with a different phone number.
                    this could happen if the user get's a new phone."""
                raise CustomUser.InconsistentPhoneNumber(email)
        except CustomUser.DoesNotExist:
            user = self.create_user(email, password, first_name,
                    last_name, phone_number)
        return user
