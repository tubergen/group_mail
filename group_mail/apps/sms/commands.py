from twilio.twiml import Response
from django.core.exceptions import ValidationError
from group_mail.apps.common.models import CustomUser, Group
#  from django.http import HttpResponse
from group_mail.apps.mailman import mailman_cmds

MAX_SMS_LEN = 160

USAGE = {'#create': '#create (group name) (group code)',
        '#join': '#join (group name) (group code)',
        '#user': '#user (email) (first name) (last name)',
        '#number': '#number (your email) (your password)',
        '#email': '#email (new email) (your password)',
        }


class Utilities(object):

    def respond(self, *args):
        r = Response()
        for msg in args:
            r.sms(msg)
        return r

    def truncate(self, text, max_len, include_ellipses=True):
        """ Truncates text to max_len. If include_ellipses is set to True,
            max_len must be >= 3 characters. """
        if len(text) > max_len:
            if include_ellipses:
                assert(max_len >= 3)
                text = text[:(max_len - 3)] + '...'
            else:
                text = text[:max_len]
        return text


class Command(Utilities):
    USAGE = None

    def __init__(self, cmd='', modify_mailman_db=True):
        self.requires_user = False
        self.expected_sms_len = None
        self.min_sms_len = None
        self.cmd = cmd
        self.modify_mailman_db = modify_mailman_db

    def get_user(self, from_number):
        try:
            user = CustomUser.objects.get(phone_number=from_number)
            return user
        except CustomUser.DoesNotExist:
            return None

    def execute(self, from_number, sms_fields):
            if self.requires_user:
                user = self.get_user(from_number)
                if user is not None:
                    return self.verify_and_execute(sms_fields, user)
                else:
                    return self.respond("We don't recognize this number. Text %s"
                        "to get set up." % NewUserCmd.USAGE)
            else:
                return self.verify_and_execute(sms_fields, from_number)

    def verify_and_execute(self, sms_fields, user_identifier):
        """ Depending on the command, user_identifier may be either the user's
            phone number or the user object itself. """

        if self.expected_sms_len and len(sms_fields) != self.expected_sms_len:
            return self.invalid_cmd()
        elif self.min_sms_len and len(sms_fields) < self.min_sms_len:
            return self.invalid_cmd()
        else:
            return self.execute_hook(sms_fields, user_identifier)

    # Subclasses should override this
    def execute_hook(self, sms_fields, user_identifier):
        return self.unrecognized_cmd()

    def valid_cmds(self):
        return '\n'.join(USAGE.values())

    def unrecognized_cmd(self):
        return self.respond('%s is not recognized.'
                    % self.truncate(self.cmd, 10) + ' Valid commands are:\n' + self.valid_cmds())

    def invalid_cmd(self):
        return self.respond("We couldn't understand your %s request." % self.cmd +
                " The proper format is:\n%s" % USAGE[self.cmd])


class CreateGroupCmd(Command):
    CMD_STR = '#create'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR, modify_mailman_db=True):
        super(CreateGroupCmd, self).__init__(cmd, modify_mailman_db)
        self.expected_sms_len = 3
        self.requires_user = True

    def _respond_too_long(self, group_attribute, text):
        return self.respond("The group %s '%s' is too long." % (group_attribute, text) + \
                " Please choose a group %s less than %d characters and try again." % \
                (group_attribute, Group.MAX_LEN))

    def execute_hook(self, sms_fields, user):
        #  ensure that the group and code specified by the user is valid
        group_name = sms_fields[1]
        group_code = sms_fields[2]
        ###
        try:
            Group.objects.create_group(user, group_name, group_code)
            return self.respond("Success! The group '%s' has been created." % group_name + \
                    ' Have members text #join (group name) (group code) to join.')
        except Group.AlreadyExists:
            return self.respond('A group with the name %s ' % group_name +
                    'already exists. Please choose a different name and try again.')
        except Group.NameTooLong:
            return self._respond_too_long('name', group_name)
        except Group.CodeTooLong:
            return self._respond_too_long('code', group_code)
        except mailman_cmds.MailmanError as e:
            return self.respond(str(e))


class JoinGroupCmd(Command):
    CMD_STR = '#user'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR, modify_mailman_db=True):
        super(JoinGroupCmd, self).__init__(cmd, modify_mailman_db)
        self.expected_sms_len = 3
        self.requires_user = True

    def execute_hook(self, sms_fields, user):
        #  ensure that the group and code specified by the user is valid
        group_name = sms_fields[1]
        group_code = sms_fields[2]
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            return self.respond("The group '%s' does not exist." % group_name)

        if group_code != group.code:
            return self.respond("The group code you entered is not correct"
                    " for the group '%s.'" % group_name)

        if user in group.members.all():
            return self.respond("You're already a member of the group '%s.'" % group_name)
        else:
            # At this point, we suspect the join group cmd is valid

            # Try modifying the mailman list first, since this is the last place
            # we expect something might go wrong
            if self.modify_mailman_db:
                errors = mailman_cmds.add_members(group_name, user.email)
                if errors:
                    return self.respond(self.truncate(', '.join(errors), MAX_SMS_LEN))

            group.members.add(user)
            return self.respond("Success! You've been added to the group '%s.'" % group_name)


class NewUserCmd(Command):
    CMD_STR = '#user'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR, modify_mailman_db=True):
        super(NewUserCmd, self).__init__(cmd, modify_mailman_db)
        self.min_sms_len = 4
        self.requires_user = False

    def execute_hook(self, sms_fields, from_number):
        # ensure that we don't accidentally pass a user into this function
        assert isinstance(from_number, str) or isinstance(from_number, unicode), \
            "from_number should be a string"

        email = sms_fields[1]
        try:
            CustomUser.objects.create_user(
                    email,
                    first_name=self.truncate(sms_fields[2], 30, False),
                    last_name=self.truncate(' '.join(sms_fields[3:]), 30, False),
                    phone_number=from_number)
        except CustomUser.DuplicatePhoneNumber:
            return self.respond('There is already an account for this phone number.'
                    ' Text %s if you want to change the email for this number.' % \
                    USAGE[ChangeEmailCmd.CMD_STR])
        except ValidationError:
            return self.respond('The email %s appears to be invalid. Please try again.' % email)
        except CustomUser.DuplicateEmail:
            return self.respond("There is already an account with this email. If the"
                    " account is your's, text %s to update the phone number for that account." % \
                    USAGE[ChangeNumberCmd.CMD_STR])

        return self.respond("Success! We've created an account for you and sent you a"
                " welcome email. You can now #join and #create groups.")


class ChangeNumberCmd(Command):
    CMD_STR = '#number'


class ChangeEmailCmd(Command):
    CMD_STR = '#email'
