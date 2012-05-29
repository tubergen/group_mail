from django.db import models
from django.conf import settings
from group_mail.apps.common.errors import CustomException
from group_mail.apps.mailman import mailman_cmds
from group_mail.apps.group.group_manager import GroupManager
from group_mail.apps.common.models import CustomUser, Email


class Group(models.Model):
    MAX_LEN = 20  # max length of group name, code
    ALLOWED_CHARS = "Only numbers and letters are allowed."
    name = models.CharField(max_length=MAX_LEN, unique=True)
    code = models.CharField(max_length=MAX_LEN)
    members = models.ManyToManyField(CustomUser, related_name='memberships')
    emails = models.ManyToManyField(Email)
    admins = models.ManyToManyField(CustomUser)

    objects = GroupManager()

    def __unicode__(self):
        return self.name

    def remove_members(self, member_email_list):
        for email in member_email_list:
            try:
                member = CustomUser.objects.get(email=email)
                self.members.remove(member)
            except CustomUser.DoesNotExist:
                pass

        if settings.MODIFY_MAILMAN_DB:
            try:
                mailman_cmds.remove_members(self.name, member_email_list)
            except mailman_cmds.MailmanError:
                raise

    def add_members(self, member_email_list):
        for email in member_email_list:
            try:
                member = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # create an account for the new user
                member = CustomUser.objects.create_user(email=email)
            self.members.add(member)
            email_obj = Email.objects.get(email=email)
            self.emails.add(email_obj)
            print email_obj

        if settings.MODIFY_MAILMAN_DB:
            try:
                mailman_cmds.add_members(self.name, member_email_list)
            except mailman_cmds.MailmanError:
                raise

    """ Custom Exceptions """

    class AlreadyExists(CustomException):
        def __init__(self, msg=None, name=''):
            if msg is None:
                msg = "A group with name '%s' already exists." % name
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
