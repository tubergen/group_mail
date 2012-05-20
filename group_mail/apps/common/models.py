from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from group_mail.apps.common.group_manager import GroupManager
from group_mail.apps.common.custom_user_manager import CustomUserManager
from group_mail.apps.mailman import mailman_cmds


class CustomUser(User):
    MAX_LEN = 128  # max length of email, password
    phone_number = models.CharField(max_length=20, blank=True)

    objects = CustomUserManager()

    def join_group(self, group_name, group_code):
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
        self.memberships.remove(group)
        if settings.MODIFY_MAILMAN_DB:
            try:
                mailman_cmds.remove_members(group.name, self.email)
            except mailman_cmds.MailmanError:
                raise

    """ Custom Exceptions """

    class _DuplicateField(Exception):
        def __init__(self, msg=None, field='field unspecified', value=''):
            if msg is None:
                msg = 'A user with the %s %s already exists.' % (field, value)
            super(CustomUser._DuplicateField, self).__init__(msg)

    class DuplicatePhoneNumber(_DuplicateField):
        def __init__(self, msg=None, phone_number=''):
            super(CustomUser.DuplicatePhoneNumber, self).__init__(msg,
                    'phone number', phone_number)

    class DuplicateEmail(_DuplicateField):
        def __init__(self, msg=None, email=''):
            super(CustomUser.DuplicateEmail, self).__init__(msg, 'email', email)

    class AlreadyMember(Exception):
        def __init__(self, msg=None, email='', group_name=''):
            if msg is None:
                msg = 'The member %s is already a member of the group %s' % \
                        (email, group_name)
            super(CustomUser.AlreadyMember, self).__init__(msg)


class Group(models.Model):
    MAX_LEN = 20  # max length of group name, code
    name = models.CharField(max_length=MAX_LEN, unique=True)
    code = models.CharField(max_length=MAX_LEN)
    members = models.ManyToManyField(CustomUser, related_name='memberships')
    admins = models.ManyToManyField(CustomUser)

    objects = GroupManager()

    def __unicode__(self):
        return self.name

    def remove_member(self, user):
        user.leave_group(self)

    """ Custom Exceptions """

    class AlreadyExists(Exception):
        def __init__(self, msg=None, name=''):
            if msg is None:
                msg = 'Group %s already exists.' % name
            super(Group.AlreadyExists, self).__init__(msg)

    class _FieldTooLong(Exception):
        def __init__(self, msg=None, field='field unspecified', value=''):
            if msg is None:
                msg = 'The group %s %s is longer than %d characters.' % \
                        (field, value, Group.MAX_LEN)
            super(Group._FieldTooLong, self).__init__(msg)

    class NameTooLong(_FieldTooLong):
        def __init__(self, msg=None, name=''):
            super(Group.NameTooLong, self).__init__(msg, 'name', name)

    class CodeTooLong(_FieldTooLong):
        def __init__(self, msg=None, code=''):
            super(Group.CodeTooLong, self).__init__(msg, 'code', code)

    class CodeInvalid(Exception):
        def __init__(self, msg=None, name='', code=''):
            if msg is None:
                msg = 'The group code %s is invalid for the group %s' % \
                        (code, name)
            super(Group.CodeInvalid, self).__init__(msg)
