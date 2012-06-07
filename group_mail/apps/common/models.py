from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from group_mail.apps.common.errors import CustomException
from group_mail.apps.common.custom_user_manager import CustomUserManager
from group_mail.apps.mailman import mailman_cmds


class CustomUser(User):
    MAX_LEN = 128  # max length of email, password
    phone_number = models.CharField(max_length=20, blank=True)

    objects = CustomUserManager()

    """
    # Remove these methods, since now we join groups with emails
    def join_group(self, group_name, group_code):
        from group_mail.apps.group.models import Group
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            raise

        if group_code != group.code:
            raise Group.CodeInvalid()

        email_obj = Email.objects.get(email=self.email)
        if email_obj in group.emails.all():
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

            group.add_members([self.email])

    def leave_group(self, group):
        group.remove_members([self.email])
    """

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

    def get_memberships(self):
        memberships = []
        for group_list in self.get_groups_by_email().values():
            for group in group_list:
                memberships.append(group)
        return memberships

    def get_groups_by_email(self):
        """
        Returns a dict of the form:
        {email1: [group1_1, group2_1, ...],
        email2: [group1_2, group2_2, ...],
        ...
        }
        This is a dictionary where each of the user's emails is a key,
        associated with a value which is a list of groups to which that email
        is subscribed.
        """
        result = {}
        for email in self.email_set.all():
            result[email] = email.group_set.all()
        return result

    """ Custom Exceptions """

    class _DuplicateField(CustomException):
        def __init__(self, msg=None, field='field unspecified', value=''):
            if msg is None:
                msg = 'An account with the %s %s already exists.' % (field, value)
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
