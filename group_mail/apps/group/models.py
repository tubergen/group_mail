from django.db import models
from django.conf import settings
from group_mail.apps.common.errors import CustomException
from group_mail.apps.mailman import mailman_cmds
from group_mail.apps.group.group_manager import GroupManager
from group_mail.apps.common.models import CustomUser, Email


class Group(models.Model):
    MAX_LEN = 20  # max length of group name, code
    ALLOWED_CHARS = "Only numbers and letters are allowed."
    name = models.CharField(max_length=MAX_LEN)
    code = models.CharField(max_length=MAX_LEN)
    # member management should go through add_members() and remove_members()
    # members = models.ManyToManyField(CustomUser, related_name='memberships')
    emails = models.ManyToManyField(Email)
    admin_emails = models.ManyToManyField(Email, related_name='groups_administrated')

    objects = GroupManager()

    def __unicode__(self):
        return self.name

    def remove_members(self, member_email_list):
        for email in member_email_list:
            try:
                email_obj = Email.objects.get(email=email)
                self.emails.remove(email_obj)
                self.admins.remove(email_obj)
            except Email.DoesNotExist:
                pass

        if settings.MODIFY_MAILMAN_DB:
            try:
                mailman_cmds.remove_members(self, member_email_list)
            except mailman_cmds.MailmanError:
                raise

    def add_members(self, member_email_list):
        for email in member_email_list:
            if not isinstance(email, basestring):
                raise TypeError('email is not a string')
            try:
                CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # create an account for the new user
                CustomUser.objects.create_user(email=email)
            email_obj = Email.objects.get(email=email)
            self.emails.add(email_obj)

        if settings.MODIFY_MAILMAN_DB:
            try:
                mailman_cmds.add_members(self, member_email_list)
            except mailman_cmds.MailmanError:
                raise

    def get_members(self):
        return [email_obj.user for email_obj in self.emails.all()]

    def add_admin_email(self, admin_email):
        try:
            admin_email_obj = Email.objects.get(email=admin_email)
        except Email.DoesNotExist:
            raise
        if admin_email_obj not in self.emails.all():
            raise CustomException('Group admin not a member of group.')
        self.admin_emails.add(admin_email_obj)

    """ Custom Exceptions """

    class AlreadyExists(CustomException):
        def __init__(self, msg=None, name='', code=''):
            if msg is None:
                msg = "A group with name '%s' and code '%s' already exists." \
                        % (name, code)
            super(Group.AlreadyExists, self).__init__(msg)

    class _FieldTooLong(CustomException):
        def __init__(self, msg=None, field='field unspecified', value=''):
            if msg is None:
                msg = 'The group %s may not exceed %d characters.' % \
                        (field, Group.MAX_LEN)
            super(Group._FieldTooLong, self).__init__(msg)

    class NameTooLong(_FieldTooLong):
        def __init__(self, msg=None, name=''):
            super(Group.NameTooLong, self).__init__(msg, 'name', name)

    class CodeTooLong(_FieldTooLong):
        def __init__(self, msg=None, code=''):
            super(Group.CodeTooLong, self).__init__(msg, 'code', code)

    class CodeInvalid(CustomException):
        def __init__(self, msg=None, name='', code=''):
            if msg is None:
                msg = 'The group code %s is invalid for the group %s' % \
                        (code, name)
            super(Group.CodeInvalid, self).__init__(msg)

    class _FieldNotAllowed(CustomException):
        def __init__(self, msg=None, field='field unspecified', value=''):
            if msg is None:
                msg = "The group %s may only contain letters and numbers." % field
            super(Group._FieldNotAllowed, self).__init__(msg)

    class NameNotAllowed(_FieldNotAllowed):
        def __init__(self, msg=None, name=''):
            super(Group.NameNotAllowed, self).__init__(msg, 'name', name)

    class CodeNotAllowed(_FieldNotAllowed):
        def __init__(self, msg=None, code=''):
            super(Group.CodeNotAllowed, self).__init__(msg, 'code', code)
