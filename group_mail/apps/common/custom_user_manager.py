# from django.conf import settings
from django.contrib.auth.models import UserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User


class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        """
        Validate that an active user exists with the given email address,
        but do not require that the user has a usuable password.
        """
        email = self.cleaned_data["email"]
        self.users_cache = User.objects.filter(email__iexact=email,
                is_active=True)
        if not len(self.users_cache):
            raise ValidationError(self.error_messages['unknown'])
        return email


class CustomUserManager(UserManager):
    def send_welcome_email(request, to_email):
        try:
            validate_email(to_email)
        except ValidationError:
            raise

        # use the password reset form to send the welcome email to easily
        # obtain password reset url
        form = CustomPasswordResetForm({'email': to_email})
        if form.is_valid():
            opts = {
                'email_template_name': 'registration/welcome_email.html',
                'subject_template_name': 'registration/welcome_subject.txt',
            }
            form.save(**opts)
        else:
            raise Exception(str(form.errors))

    def get(self, *args, **kwargs):
        """
        Override the default get() method so that we can check all the emails
        in the system (including those in email_set) for a user, not just
        the primary emails stored in the email field.
        """
        from group_mail.apps.common.models import CustomUser, Email
        try:
            return super(CustomUserManager, self).get(*args, **kwargs)
        except CustomUser.DoesNotExist:
            pass

        if 'email' in kwargs.keys():
            try:
                # if this email is in some user's email set, we want to
                # return that user
                email_object = Email.objects.get(email=kwargs['email'])
                return email_object.user
            except Email.DoesNotExist:
                pass

        raise CustomUser.DoesNotExist

    def get_user(self, **kwargs):
        """
        Get's and returns a user object according to field_dict, or returns
        None if no such user exists.

        field_dict must be of the form {'user_field': value},
        e.g.: {'email': 'me@gmail.com'}
        """
        from group_mail.apps.common.models import CustomUser

        try:
            return CustomUser.objects.get(**kwargs)
        except CustomUser.DoesNotExist:
            return None

    """ Helper methods """

    def create_user(self, email, password=None, first_name=None, last_name=None, phone_number=None):
        """
        Creates a CustomUser with the values given by the parameters and returns
        the CustomUser if successful.
        """
        from group_mail.apps.common.models import CustomUser

        # validate the email
        try:
            validate_email(email)
        except ValidationError:
            raise

        user = self.get_user(email=email)
        if user:
            raise CustomUser.DuplicateEmail(email=email)
        else:
            p_user = self.get_user(phone_number=phone_number)
            if p_user:
                """
                We're trying to create a user with a new email but same phone number as
                another account.
                """
                raise CustomUser.DuplicatePhoneNumber(phone_number=phone_number)

        user = super(CustomUserManager, self).create_user(
                username=email,
                email=email,
                password=password)
        user.populate(email, first_name, last_name, phone_number)
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

        user = self.get_user(email=email)
        p_user = self.get_user(phone_number=phone_number)

        if user and p_user:
            if p_user.id != user.id:
                """
                we've specified an existent email for which the associated
                phone number does not match.
                """
                raise CustomUser.InconsistentPhoneNumber(email=email)
        elif p_user and not user:
            """
            there's an account with this phone number, but not this email.
            populate the account with the new email (and other info if provided).
            """
            user = p_user
            user.populate(email, first_name, last_name, phone_number)
        elif user and not p_user:
            """
            there's an account with this email, but not this phone number.
            we want to raise an error so that the user must confirm the number.
            """
            raise CustomUser.InconsistentPhoneNumber(email=email)
        else:
            user = self.create_user(email, password, phone_number)

        return user
