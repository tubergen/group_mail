from django.db import models
from django.conf import settings
from group_mail.apps.mailman import mailman_cmds


class GroupManager(models.Manager):
    def create_group(self, creator, group_name, group_code):
        # we do the import here to avoid a circular dependency
        from group_mail.apps.common.models import Group

        try:
            group = Group.objects.get(name=group_name)
            raise Group.AlreadyExists(name=group_name)
        except Group.DoesNotExist:
            if len(group_name) > Group.MAX_LEN:
                raise Group.NameTooLong(name=group_name)

            if len(group_code) > Group.MAX_LEN:
                raise Group.CodeTooLong(code=group_code)

            # At this point, we suspect the group creation is valid

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
