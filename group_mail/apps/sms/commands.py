from twilio.twiml import Response
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from group_mail.apps.sms.models import CustomUser, Group
#  from django.http import HttpResponse


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
        if len(text) > max_len:
            if include_ellipses:
                text = text[:(max_len - 3)] + '...'
            else:
                text = text[:max_len]
        return text

    def check_email(self, email):
        resp = None
        try:
            validate_email(email)
        except ValidationError:
            resp = 'The email %s appears to be invalid. Please try again.' % email
        return resp


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
        user = self.get_user(from_number)

        if user is None:
            if self.requires_user:
                return self.respond("We don't recognize this number. Text %s"
                        "to get set up." % NewUserCmd.USAGE)
            else:
                return self.verify_and_execute(sms_fields, from_number)

        return self.verify_and_execute(sms_fields, user)

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
        return self.respond('The command %s is not recognized. Please try again.'
                % self.truncate(self.cmd, 10) + ' Valid commands are:\n' + self.valid_cmds())

    def invalid_cmd(self):
        return self.respond("We couldn't understand your %s request." % self.cmd +
                " The proper format is:\n%s" % USAGE[self.cmd])


class CreateGroupCmd(Command):
    CMD_STR = '#create'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR):
        super(CreateGroupCmd, self).__init__(cmd)
        self.expected_sms_len = 3
        self.requires_user = True

    def validate_length(self, text, text_name, max_len):
        resp = None
        if len(text) > max_len:
            resp = "The %s '%s' is too long." % (text_name, text) + \
                   " Please choose a %s less than %d characters and try again." % \
                   (text_name, max_len)
        return resp

    def execute_hook(self, sms_fields, user):
        #  ensure that the group and code specified by the user is valid
        group_name = sms_fields[1]
        group_code = sms_fields[2]
        try:
            group = Group.objects.get(name=group_name)
            return self.respond('A group with the name %s ' % group_name +
                    'already exists. Please choose a different name and try again.')
        except Group.DoesNotExist:
            resp = self.validate_length(group_name, 'name', Group.MAX_LEN)
            if resp is not None:
                return self.respond(resp)

            resp = self.validate_length(group_code, 'code', Group.MAX_LEN)
            if resp is not None:
                return self.respond(resp)

            group = Group.objects.create(name=group_name,
                                         code=group_code)

        group.members.add(user)
        group.admins.add(user)
        return self.respond("Success! The group '%s' has been created." % group_name + \
                ' Have members text #join (group name) (group code) to join.')


class JoinGroupCmd(Command):
    CMD_STR = '#user'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR):
        super(JoinGroupCmd, self).__init__(cmd)
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
            group.members.add(user)
            return self.respond("Success! You've been added to the group '%s.'" % group_name)


class NewUserCmd(Command):
    CMD_STR = '#user'
    USAGE = USAGE[CMD_STR]

    def __init__(self, cmd=CMD_STR):
        super(NewUserCmd, self).__init__(cmd)
        self.min_sms_len = 4
        self.requires_user = False

    def execute_hook(self, sms_fields, from_number):
        if self.get_user(from_number) is not None:
            return self.respond('There is already an account for this phone number.'
                    ' Text %s if you want to change the email for this number.' % \
                    USAGE[ChangeEmailCmd.CMD_STR])

        email = sms_fields[1]
        resp = self.check_email(email)
        if resp is not None:
            return self.respond(resp)

        try:
            CustomUser.objects.get(email=email)
            return self.respond("There is already an account with this email. If the"
                    " account is your's, text %s to update the phone number for that account." % \
                    USAGE[ChangeNumberCmd.CMD_STR])

        except CustomUser.DoesNotExist:
            CustomUser.objects.create(username=email,
                    first_name=self.truncate(sms_fields[2], 30, False),
                    last_name=self.truncate(sms_fields[3:], 30, False),
                    email=email,
                    phone_number=from_number)

            #  TODO: actually send welcome email

            return self.respond("Success! We've created an account for you and sent you a"
                    " welcome email. You can now #join and #create groups.")


class ChangeNumberCmd(Command):
    CMD_STR = '#number'


class ChangeEmailCmd(Command):
    CMD_STR = '#email'
