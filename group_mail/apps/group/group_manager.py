import re
from django.db import models
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from group_mail.apps.mailman import mailman_cmds
from group_mail.apps.sms.commands import CreateGroupCmd, JoinGroupCmd


class GroupManager(models.Manager):

    valid_pattern = '^[\w\d]+$'

    def send_group_confirm_email(self, cmd_str, group_name, group_code, email):
        """
        Sends an email to the user letting him know that he
        created or was added to the group (depending on the value of
        create_or_join).

        This email let's the user confirm his action.

        We send this when
        1) the user tries to join a group from a phone number we don't recognize
        2) somebody adds the user to the group
        """
        from django.core.mail import send_mail
        from django.template import loader
        try:
            validate_email(email)
        except ValidationError:
            raise
        current_site = Site.objects.get_current()
        url = self._get_confirm_url(cmd_str, group_name, group_code, email)
        c = {
            'cmd_str': cmd_str,
            'email': email,
            'group_name': group_name,
            'group_code': group_code,
            'site_name': current_site.name,
            'confirm_group_url': url
        }

        subject = loader.render_to_string('group/group_confirm_subject.html', c)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        email = loader.render_to_string('group/group_confirm_email.html', c)
        # send_mail(subject, email, from_email, [claim_email_addr])
        send_mail(subject, email, None, ['brian.tubergen@gmail.com'])

    def _get_confirm_url(self, cmd_str, group_name, group_code, email):
        """
        Returns the group confirm url for the given cmd_str. Populates
        the GET parameters of the url according to other arguments.

        This probably isn't the right way to get the url for the group
        confirm email, but it's easy.
        """
        if cmd_str == CreateGroupCmd.CMD_STR:
            url = reverse('group_mail.apps.group.views.create_group')
        elif cmd_str == JoinGroupCmd.CMD_STR:
            url = reverse('group_mail.apps.group.views.join_group')
        url += ('?group_name=%s&group_code=%s&email=%s' % \
                (group_name, group_code, email))
        return url

    def validate_group(self, group_name, group_code):
        self.validate_group_uniqueness(group_name, group_code)
        self.validate_group_name(group_name)
        self.validate_group_code(group_code)

    def validate_group_uniqueness(self, group_name, group_code):
        from group_mail.apps.group.models import Group
        try:
            Group.objects.get(name=group_name, code=group_code)
            raise Group.AlreadyExists(name=group_name, code=group_code)
        except Group.DoesNotExist:
            pass

    def validate_group_name(self, group_name):
        from group_mail.apps.group.models import Group
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
            self.validate_group(group_name, group_code)
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

    def get_group_for_email(self, email_list, group_name):
        """
        Returns the name of the group with name group_name to which
        some email_obj in email_list is subscribed.
        """
        for email_obj in email_list:
            for group in email_obj.group_set.all():
                if group.name == group_name:
                    return group
        return None
