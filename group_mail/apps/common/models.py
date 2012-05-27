from django.db import models, IntegrityError
from django.contrib.auth.models import User
from django.conf import settings
from group_mail.apps.common.errors import CustomException
from group_mail.apps.common.custom_user_manager import CustomUserManager
from group_mail.apps.mailman import mailman_cmds


class CustomUser(User):
    MAX_LEN = 128  # max length of email, password
    phone_number = models.CharField(max_length=20, blank=True)

    objects = CustomUserManager()

    def join_group(self, group_name, group_code):
        from group_mail.apps.group.models import Group
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            raise

        if group_code != group.code:
            raise Group.CodeInvalid()

        if group in self.memberships.all():
            raise CustomUser.AlreadyMember(self.email, group_name)
        else:
            # At this point, we suspect the join group cmd is valid

            # Try modifying the mailman list first, since this is the last place
            # we expect something might go wrong
            if settings.MODIFY_MAILMAN_DB:
                try:
                    mailman_cmds.add_members(group_name, self.email)
                except mailman_cmds.MailmanError:
                    raise

            self.memberships.add(group)

    def leave_group(self, group):
        group.remove_members([self])

    def is_complete(self):
        """ returns true if the CustomUser has a complete account
            (all #user cmd info populated) and false otherwise """
        if self.first_name and self.last_name and self.phone_number:
            return True
        else:
            return False

    def populate(self, email=None, first_name=None, last_name=None, phone_number=None):
        if email:
            # check if this account already has the email
            try:
                found_email = self.email_set.get(email=email)
            except Email.DoesNotExist:
                found_email = None

            if not found_email:
                # This will raise an IntegrityError if the email object already exists
                Email.objects.create(email=email, user=self)

        if first_name and not self.first_name:
            self.first_name = first_name
        if last_name and not self.last_name:
            self.last_name = last_name
        if phone_number and not self.phone_number:
            self.phone_number = phone_number
        self.save()

    """ Custom Exceptions """

    class _DuplicateField(CustomException):
        def __init__(self, msg=None, field='field unspecified', value=''):
            if msg is None:
                msg = 'A user with the %s %s already exists.' % (field, value)
            super(CustomUser._DuplicateField, self).__init__(msg)

    class DuplicatePhoneNumber(_DuplicateField):
        def __init__(self, msg=None, phone_number=''):
            super(CustomUser.DuplicatePhoneNumber, self).__init__(msg, 'phone number', phone_number)

    class DuplicateEmail(_DuplicateField):
        def __init__(self, msg=None, email=''):
            super(CustomUser.DuplicateEmail, self).__init__(msg, 'email', email)

    class AlreadyMember(CustomException):
        def __init__(self, msg=None, email='', group_name=''):
            if msg is None:
                msg = 'The member %s is already a member of the group %s' % \
                        (email, group_name)
            super(CustomUser.AlreadyMember, self).__init__(msg)

    class InconsistentPhoneNumber(CustomException):
        def __init__(self, msg=None, email=''):
            if msg is None:
                msg = 'The email %s is associated with a different phone number.' % \
                        email
            super(CustomUser.InconsistentPhoneNumber, self).__init__(msg)


class Email(models.Model):
    email = models.EmailField(unique=True)
    user = models.ForeignKey(CustomUser, related_name='email_set')

    def __unicode__(self):
        return self.email
