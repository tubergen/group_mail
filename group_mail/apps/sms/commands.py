from twilio.twiml import Response
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
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

    def get_or_create_user(self, email, from_number):
        user = None
        resp = None
        try:
            user = CustomUser.objects.get_or_create_user(email=email, phone_number=from_number)
        except CustomUser.InconsistentPhoneNumber, e:
            domain = Site.objects.get_current().domain
            resp = self.respond(str(e) + 'Go to %s, register or login to an account, and' % domain +
                    ' go to your profile to change the phone number.')
        except CustomUser.DuplicatePhoneNumber:
            resp = self.respond('There is already an account for this phone number.'
                    ' Text %s if you want to change the email for this number.' % \
                    USAGE[ChangeEmailCmd.CMD_STR])
        except ValidationError:
            resp = self.respond('The email %s appears to be invalid. Please try again.' % \
                    email)
        except CustomUser.DuplicateEmail:
            resp = self.respond("There is already an account with this email. If the"
                    " account is your's, text %s to update the phone number for that account." % \
                    USAGE[ChangeNumberCmd.CMD_STR])
        return user, resp


class Command(Utilities):
    USAGE = None

    def __init__(self, cmd=''):
        self.requires_user = False
        self.expected_sms_len = None
        self.min_sms_len = None
        self.cmd = cmd

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

    def __init__(self, cmd=CMD_STR):
        super(CreateGroupCmd, self).__init__(cmd)
        self.expected_sms_len = 4
        # self.requires_user = True

    def _respond_too_long(self, group_field, text):
        return self.respond("The group %s '%s' is too long." % (group_field, text) + \
                " Please choose a group %s less than %d characters and try again." % \
                (group_field, Group.MAX_LEN))

    def execute_hook(self, sms_fields, from_number):
        #  ensure that the group and code specified by the user is valid
        group_name = sms_fields[1]
        group_code = sms_fields[2]
        email = sms_fields[3]

        user, resp = self.get_or_create_user(email, from_number)
        if resp:  # if there was an error
            return resp

        ###
        try:
            Group.objects.create_group(user, group_name, group_code)
            return self.respond("Success! The group '%s' has been created." % group_name + \
                    ' Have members text #join (group name) (group code) to join.')
        except Group.AlreadyExists as e:
            return self.respond(str(e) + \
                    'Please choose a different name and try again.')
        except Group.NameTooLong:
            return self._respond_too_long('name', group_name)
        except Group.CodeTooLong:
            return self._respond_too_long('code', group_code)
        except Group.NameNotAllowed as e:
            return self.respond(str(e))
        except Group.CodeNotAllowed as e:
            return self.respond(str(e))
        except mailman_cmds.MailmanError as e:
            return self.respond(str(e))


class JoinGroupCmd(Command):
    CMD_STR = '#user'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR):
        super(JoinGroupCmd, self).__init__(cmd)
        self.expected_sms_len = 3
        self.requires_user = True

    def execute_hook(self, sms_fields, user):
        group_name = sms_fields[1]
        try:
            user.join_group(group_name, group_code=sms_fields[2])
        except Group.DoesNotExist:
            return self.respond("The group '%s' does not exist." % group_name)
        except Group.CodeInvalid:
            return self.respond("The group code you entered is not correct"
                    " for the group '%s.'" % group_name)
        except CustomUser.AlreadyMember:
            return self.respond("You're already a member of the group '%s.'" % group_name)

        return self.respond("Success! You've been added to the group '%s.'" % group_name)


class NewUserCmd(Command):
    CMD_STR = '#user'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR):
        super(NewUserCmd, self).__init__(cmd)
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
