from django.db import models
from django.contrib.auth.models import User, UserManager
from group_mail.apps.common.GroupManager import GroupManager


class CustomUser(User):
    phone_number = models.CharField(max_length=20)

    objects = UserManager()


class Group(models.Model):
    MAX_LEN = 20
    name = models.CharField(max_length=MAX_LEN, unique=True)
    code = models.CharField(max_length=MAX_LEN)
    members = models.ManyToManyField(CustomUser, related_name='memberships')
    admins = models.ManyToManyField(CustomUser)

    objects = GroupManager()

    def __unicode__(self):
        return self.name

    """ Custom Exceptions """

    class AlreadyExists(Exception):
        def __init__(self, msg=None):
            if msg is None:
                msg = 'Group already exists.'
            super(Group.AlreadyExists, self).__init__(msg)

        def __str__(self):
            return repr(self.msg)

    class _FieldTooLong(Exception):
        def __init__(self, msg=None, field='field unspecified'):
            if msg is None:
                msg = 'Group %s is longer than %d characters.' % \
                        (field, Group.MAX_LEN)
            super(Group._FieldTooLong, self).__init__(msg)

        def __str__(self):
            return repr(self.msg)

    class NameTooLong(_FieldTooLong):
        def __init__(self, msg=None):
            super(Group.NameTooLong, self).__init__(msg, 'name')

        def __str__(self):
            return repr(self.msg)

    class CodeTooLong(_FieldTooLong):
        def __init__(self, msg=None):
            super(Group.CodeTooLong, self).__init__(msg, 'code')

        def __str__(self):
            return repr(self.msg)
