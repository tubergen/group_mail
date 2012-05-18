from django.db import models
from group_mail.apps.mailman import mailman_cmds
from django.conf import settings


class GroupManager(models.Manager):

    def validate_length(self, text, text_name, max_len):
        resp = None
        if len(text) > max_len:
            resp = "The %s '%s' is too long." % (text_name, text) + \
                   " Please choose a %s less than %d characters and try again." % \
                   (text_name, max_len)
        return resp

    def create_group(self, creator, group_name, group_code):
        # we do the import here to avoid a circular dependency
        from group_mail.apps.common.models import Group

        try:
            group = Group.objects.get(name=group_name)
            raise Group.AlreadyExists()
        except Group.DoesNotExist:
            resp = self.validate_length(group_name, 'name', Group.MAX_LEN)
            if resp is not None:
                raise Group.NameTooLong()

            resp = self.validate_length(group_code, 'code', Group.MAX_LEN)
            if resp is not None:
                raise Group.CodeTooLong()

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
