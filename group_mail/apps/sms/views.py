from twilio.twiml import Response
from django_twilio.decorators import twilio_view
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from group_mail.apps.sms.models import CustomUser


# Forward declarations

def join_group_cmd(*args):
    join_group(args)


def create_group_cmd(*args):
    create_group(args)


def new_user_cmd(*args):
    new_user(args)


STATES = "POST_EMAIL_STATE", "POST_NAME_STATE"

COMMANDS = {'#create': create_group_cmd, '#join': join_group_cmd,
            '#user': new_user_cmd}

USAGE = {'#create': '#create (group name) (group code)',
         '#join': '#join (group name) (group code)',
         '#user': '#user (email) (first name) (last name)'}


@twilio_view
def parse_sms(request):
    return unrecognized_cmd('hi')
    from_number = request.POST.get('From', '')
    if from_number == '':
        return  # ignore request

    sms_data = request.POST.get('Body', '')
    sms_fields = sms_data.split()
    if len(sms_fields) > 0:
        cmd = sms_fields[0]

        # validate user
        try:
            user = CustomUser.objects.get(phone_number=from_number)
        except CustomUser.DoesNotExist:
            if cmd == '#user':
                return new_user(from_number, sms_fields)
            else:
                return respond("We don't recognize this number. Text " +
                    USAGE['#user'] + " to get set up.")

        # validate command
        if cmd in COMMANDS.keys():
            return COMMANDS[cmd](user, sms_fields)
        else:
            return unrecognized_cmd(cmd)
    else:
        pass  # msg was empty, so ignore


def valid_cmds():
    return '\n'.join(USAGE.values())


def unrecognized_cmd(cmd):
    return respond('The command ' + truncate(cmd, 10) + ' is not'
            + ' recognized. Please try again. ' +
            'Valid commands are:\n' + valid_cmds())


def new_user(from_number, sms_fields):
    min_sms_len = 4
    if len(sms_fields) < min_sms_len:
        return invalid_cmd(sms_fields[0])

    try:
        email = sms_fields[1]
        validate_email(email)
    except ValidationError:
        return respond('The email "' + sms_fields[1] + '" appears to be invalid.' +
                ' Please try again.')

    CustomUser.objects.create(username=email,
            first_name=truncate(sms_fields[2], 30, False),
            last_name=truncate(sms_fields[3:], 30, False),
            email=email,
            phone_number=from_number)

    #  TODO: actually send welcome email

    return respond("Success! We've created an account for you and sent you a" +
            " welcome email. You can now #join and #create groups.")


def truncate(text, max_len, include_ellipses=True):
    if len(text) > max_len:
        if include_ellipses:
            text = text[:(max_len - 3)] + '...'
        else:
            text = text[:max_len]

    return text


def respond(msg):
    r = Response()
    r.sms(msg)
    return r


def invalid_cmd(cmd):
    return respond("We couldn't understand your " + cmd + " request."
            + " The proper format is:\n" + USAGE[cmd])


def join_group(user, sms_fields):
    pass
    """
    expected_sms_len = 3
    if len(sms_fields) != expected_sms_len:
        return invalid_cmd(sms_fields[0])

    #  ensure that the group and code specified by the user is valid

    group_name = sms_fields[1]
    group_code = sms_fields[2]
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return respond('The group ' + group_name + ' does not exist.')

    if group_code != group.code:
        return respond ('The group code you entered is not correct' +
                ' for the group ' + group_name + '.')

    group.members.add(user)
    return 'generic response'
    """


def create_group(*args):
    pass


"""
@twilio_view
def reply_to_sms_messages(request):

    user = CustomUser.objects.filter(phone_number=from_number)
    if len(user) == 0:
        # new user, so prompt for name/email

    elif len(user) == 1:
        # return user, so just add him to group
        user = user[0]
    else:
        # we have a database problem
        return


    r = Response()
    r.sms('Thanks for the SMS message, ' + fromVar + '!')
    r.sms('You wrote... ' + data)
    return r
"""
