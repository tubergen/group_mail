from twilio.twiml import Response
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
from group_mail.apps.common.models import CustomUser, Group
#  from django.http import HttpResponse
from group_mail.apps.mailman import mailman_cmds

MAX_SMS_LEN = 160

USAGE = {'#create': '#create (group name) (group code) (your email)',
        '#join': '#join (group name) (group code) (your email)',
        }


class Utilities(object):

    def respond(self, *args):
        r = Response()
        for msg in reversed(args):
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
        except CustomUser.InconsistentPhoneNumber as e:
            domain = Site.objects.get_current().domain
            resp = self.respond(str(e), ' Go to %s, log in or create an account, and' % domain +
                    ' go to you profile to change the phone number.')
        except CustomUser.DuplicatePhoneNumber as e:
            resp = self.respond(str(e) + ' TODO: This response is deprecated; needs to be removed/fixed.')
        except ValidationError as e:
            # TODO: validation error is no longer specific to email. This
            # could be another error. We need a way to be more certain.
            resp = self.respond('The email %s appears to be invalid. Please try again.' % email)
        return user, resp


class Command(Utilities):
    USAGE = None

    def __init__(self, cmd=''):
        self.expected_sms_len = None
        self.cmd = cmd

    def get_user(self, from_number):
        try:
            user = CustomUser.objects.get(phone_number=from_number)
            return user
        except CustomUser.DoesNotExist:
            return None

    def get_cmd_info(self, sms_fields, from_number):
        email = sms_fields[3]
        user, resp = self.get_or_create_user(email, from_number)
        return {'group_name': sms_fields[1], 'group_code': sms_fields[2], 'user': user}, resp

    def execute(self, sms_fields, from_number):
        if self.expected_sms_len and len(sms_fields) != self.expected_sms_len:
            return self.invalid_cmd(sms_fields)
        else:
            kwargs, resp = self.get_cmd_info(sms_fields, from_number)
            if resp:  # if there was an error
                return resp
            else:
                return self.execute_hook(**kwargs)

    # Subclasses should override this
    def execute_hook(self, sms_fields, user_identifier):
        return self.unrecognized_cmd()

    def valid_cmds(self):
        return '\n'.join(USAGE.values())

    def unrecognized_cmd(self):
        return self.respond('%s is not recognized.'
                    % self.truncate(self.cmd, 10) + ' Valid commands are:\n' + self.valid_cmds())

    def invalid_cmd(self, sms_fields):
        return self.respond("We couldn't understand your %s request." % self.cmd +
                " The proper format is:\n%s" % USAGE[self.cmd] + str(sms_fields))


class CreateGroupCmd(Command):
    CMD_STR = '#create'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR):
        super(CreateGroupCmd, self).__init__(cmd)
        self.expected_sms_len = 4

    def _respond_too_long(self, group_field, text):
        return self.respond("The group %s '%s' is too long." % (group_field, text) + \
                " Please choose a group %s less than %d characters and try again." % \
                (group_field, Group.MAX_LEN))

    def execute_hook(self, group_name, group_code, user):
        try:
            Group.objects.create_group(user, group_name, group_code)
            return self.respond("Success! The group '%s' has been created." % group_name + \
                    ' Have members text #join (group name) (group code) to join.')
        except Group.AlreadyExists as e:
            return self.respond(str(e) + \
                    ' Please choose a different name and try again.')
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
    CMD_STR = '#join'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR):
        super(JoinGroupCmd, self).__init__(cmd)
        self.expected_sms_len = 4

    def execute_hook(self, group_name, group_code, user):
        try:
            user.join_group(group_name, group_code)
            return self.respond("Success! You've been added to the group '%s.'" % group_name)
        except Group.DoesNotExist:
            return self.respond("The group '%s' does not exist." % group_name)
        except Group.CodeInvalid:
            return self.respond("The group code you entered is not correct"
                    " for the group '%s.'" % group_name)
        except CustomUser.AlreadyMember:
            return self.respond("You're already a member of the group '%s.'" % group_name)
