import re
from django.db import models
from django.conf import settings
from group_mail.apps.mailman import mailman_cmds


class GroupManager(models.Manager):

    valid_pattern = '^[\w\d]+$'

    # we do import within methods to avoid a circular dependency
    def validate_group_name(self, group_name):
        from group_mail.apps.common.models import Group
        try:
            Group.objects.get(name=group_name)
            raise Group.AlreadyExists(name=group_name)
        except Group.DoesNotExist:
            pass

        if len(group_name) > Group.MAX_LEN:
            raise Group.NameTooLong(name=group_name)
        elif not re.match(GroupManager.valid_pattern, group_name):
            raise Group.NameNotAllowed(name=group_name)

    def validate_group_code(self, group_code):
        from group_mail.apps.common.models import Group
        if len(group_code) > Group.MAX_LEN:
            raise Group.CodeTooLong(code=group_code)
        elif not re.match(GroupManager.valid_pattern, group_code):
            raise Group.CodeNotAllowed(code=group_code)

    def create_group(self, creator, group_name, group_code):
        from group_mail.apps.common.models import Group

        group_name = group_name.strip()
        group_code = group_code.strip()

        try:
            self.validate_group_name(group_name)
            self.validate_group_code(group_code)
        except Exception:
            raise

        # Try creating the mailman list first, since this is the last place
        # we expect something might go wrong
        if settings.MODIFY_MAILMAN_DB:
            try:
                mailman_cmds.newlist(group_name, creator.email, group_code)
            except mailman_cmds.MailmanError:
                raise

        group = Group.objects.create(name=group_name,
                                        code=group_code)

        group.members.add(creator)
        group.admins.add(creator)
        return group
