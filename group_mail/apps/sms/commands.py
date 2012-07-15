from twilio.twiml import Response
from django.core.exceptions import ValidationError
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.models import Group
from group_mail.apps.mailman import mailman_cmds

MAX_SMS_LEN = 160

USAGE = {'#create': '#create (group name) (group code) (your email)',
        '#join': '#join (group name) (group code) (your email)',
        }


class Utilities(object):

    def respond(self, *args):
        r = Response()
        for msg in reversed(args):
            for text_msg in self.truncate_msg(msg):
                r.sms(text_msg)
        return r

    def truncate_msg(self, text):
        """
        Truncates text to MAX_SMS_LEN.

        This function won't work properly if the messge needs to be broken
        into more than 9 chunks.
        """
        text_len = len(text)
        if text_len <= MAX_SMS_LEN:
            return text

        # break the text message into chunks
        paren_format = '(X/Y) '
        max_len = MAX_SMS_LEN - len(paren_format)
        start = 0
        chunks = []
        done = False
        while start < text_len and not done:
            end = min(start + max_len, text_len)
            chunk = text[start:end]
            if end != text_len:
                last_space = chunk.rfind(' ')
                chunk = chunk[0:last_space]  # don't cut off the middle of a word
                start = last_space + 1
            else:
                done = True
            chunks.append(chunk)

        # append the (X/Y)
        num_chunks = len(chunks)
        for i in range(0, num_chunks):
            chunks[i] = '(%d/%d) ' % (i + 1, num_chunks) + chunks[i]
        return chunks

    def truncate(self, text, max_len, include_ellipses=True):
        if len(text) > max_len:
            if include_ellipses:
                assert(max_len >= 3)
                text = text[:(max_len - 3)] + '...'
            else:
                text = text[:max_len]
        return text


class Command(Utilities):
    CMD_STR = None
    USAGE = None

    def __init__(self, cmd=''):
        self.expected_sms_len = None
        self.cmd = cmd

    def invalid_email_resp(self, email):
        return self.respond('The email %s appears to be invalid. Please try again.' % email)

    def get_or_create_user(self, sms_dict, from_number):
        """
        SMS dict should be of the form:
            {'cmd_str': value, 'group_name': value, 'group_code': value, 'email': value}
        """
        user = None
        resp = None
        email = sms_dict['email']
        try:
            user = CustomUser.objects.get_or_create_user(email=email, phone_number=from_number)
        except CustomUser.InconsistentPhoneNumber as e:
            resp = self.respond(str(e) + " We'll send you an email with instructions about how"
                    " to confirm your identity and %s the group." % str(self))
            try:
                Group.objects.send_group_confirm_email(**sms_dict)
            except ValidationError:
                resp = self.invalid_email_resp(email)
        except CustomUser.DuplicateEmail:
            raise  # this case should never arise. we should get the user with that email.
        except CustomUser.DuplicatePhoneNumber:
            raise  # this case should never arise. we shuold get the user with that phone number.
        except ValidationError:
            # TODO: validation error is no longer specific to email. This
            # could be another error. We need a way to be more certain.
            resp = self.invalid_email_resp(email)
        return user, resp

    def get_cmd_info(self, sms_fields, from_number):
        sms_dict = {'cmd_str': self.CMD_STR, 'group_name': sms_fields[1],
            'group_code': sms_fields[2], 'email': sms_fields[3]}
        # we don't use the user, but we still call get_or_create_user() to make sure
        # that the user's account exists, or to create an account if it doesn't
        user, resp = self.get_or_create_user(sms_dict, from_number)
        return sms_dict, resp

    def execute(self, sms_fields, from_number):
        if self.expected_sms_len and len(sms_fields) != self.expected_sms_len:
            return self.invalid_cmd(sms_fields)
        else:
            kwargs, resp = self.get_cmd_info(sms_fields, from_number)
            del kwargs['cmd_str']  # execute_hook doesn't take cmd_str as a parameter
            if resp:  # if there was an error
                return resp
            else:
                return self.execute_hook(**kwargs)

    # Subclasses should override this
    def execute_hook(self, *args, **kwargs):
        return self.unrecognized_cmd()

    def valid_cmds(self):
        return '\n'.join(USAGE.values())

    def unrecognized_cmd(self):
        return self.respond('%s is not recognized.'
                    % self.truncate(self.cmd, 10) + ' Valid commands are:\n' + self.valid_cmds())

    def invalid_cmd(self, sms_fields):
        return self.respond("We couldn't understand your %s request." % self.cmd +
                " The proper format is:\n%s" % USAGE[self.cmd] + str(sms_fields))

    def __str__(self):
        return self.CMD_STR


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

    def execute_hook(self, group_name, group_code, email):
        try:
            Group.objects.create_group(email, group_name, group_code)
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

    def execute_hook(self, group_name, group_code, email):
        try:
            group = Group.objects.get(name=group_name, code=group_code)
            group.add_members([email])
            return self.respond("Success! You've been added to the group '%s.'" % group_name)
        except Group.DoesNotExist:
            try:
                Group.objects.get(name=group_name)
                # there is a group with this name, so the code must be invalid
                return self.respond("The group code you entered is not correct"
                    " for the group '%s.'" % group_name)
            except Group.DoesNotExist:
                return self.respond("The group '%s' does not exist." % group_name)
        """
        Decided we don't need this case. Just return success, even if they've already joined.
        except CustomUser.AlreadyMember:
            return self.respond("You're already a member of the group '%s.'" % group_name)
        """
