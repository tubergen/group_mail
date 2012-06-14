import re
from django.db import models
from django.conf import settings
from group_mail.apps.mailman import mailman_cmds


class GroupManager(models.Manager):

    valid_pattern = '^[\w\d]+$'

    # we do import within methods to avoid a circular dependency
    def validate_group_name(self, group_name):
        from group_mail.apps.group.models import Group
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
        from group_mail.apps.group.models import Group
        if len(group_code) > Group.MAX_LEN:
            raise Group.CodeTooLong(code=group_code)
        elif not re.match(GroupManager.valid_pattern, group_code):
            raise Group.CodeNotAllowed(code=group_code)

    def create_group(self, creator_email, group_name, group_code):
        from group_mail.apps.group.models import Group

        group_name = group_name.strip()
        group_code = group_code.strip()

        try:
            self.validate_group_name(group_name)
            self.validate_group_code(group_code)
        except Exception:
            raise

        # we must create the group before the mailman list to get its id
        group = Group.objects.create(name=group_name,
                                    code=group_code)

        # Try creating the mailman list first, since this is the last place
        # we expect something might go wrong
        if settings.MODIFY_MAILMAN_DB:
            try:
                mailman_cmds.newlist(group)
            except mailman_cmds.MailmanError:
                raise

        # add_members has to come after we make the mailman list, since it will
        # try to add members to the mailman list
        group.add_members([creator_email])
        group.add_admin_email(creator_email)
        return group
