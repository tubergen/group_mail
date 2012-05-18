from django.http import Http404, HttpResponse
from twilio.twiml import Response
from django_twilio.decorators import twilio_view
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from group_mail.apps.common.models import CustomUser
from group_mail.apps.sms.commands import Command, CreateGroupCmd, JoinGroupCmd, NewUserCmd, ChangeNumberCmd

# Forward declarations


def join_group_cmd(*args):
    join_group(args)


def create_group_cmd(*args):
    create_group(args)


def new_user_cmd(*args):
    new_user(args)


def change_phone_number_cmd(*args):
    change_phone_number(args)


STATES = "GET_EMAIL_STATE", "GET_NAME_STATE"

COMMANDS = {'#create': create_group_cmd, '#join': join_group_cmd,
        '#user': new_user_cmd, '#number': change_phone_number_cmd}

USAGE = {'#create': '#create (group name) (group code)',
         '#join': '#join (group name) (group code)',
         '#user': '#user (email) (first name) (last name)',
         '#number': '#number (your email) (your password)'}


COMMAND_CLASSES = {'#create': CreateGroupCmd, '#join': JoinGroupCmd,
        '#user': NewUserCmd, '#number': ChangeNumberCmd}


@twilio_view
def parse_sms(request):
    from_number = request.GET.get('From', '')
    sms_data = request.GET.get('Body', '')
    #  return respond(sms_data)
    if from_number != '' and sms_data != '':
        sms_fields = sms_data.split()
        cmd = COMMAND_CLASSES.get(sms_fields[0], Command)(sms_fields[0])
        return cmd.execute(from_number, sms_fields)

    raise Http404
    """

        # validate user
        try:
            user = CustomUser.objects.get(phone_number=from_number)
        except CustomUser.DoesNotExist:
            if cmd == '#user' or cmd == '#number':
                return verify(cmd, from_number, sms_fields)
            else:
                return respond("We don't recognize this number. Text " +
                    USAGE['#user'] + " to get set up.")

        # validate command
        if cmd in COMMANDS.keys():
            return verify(cmd, user, sms_fields))
        else:
            return unrecognized_cmd(cmd)
    else:
        pass  # msg was empty, so ignore

    """


def verify(cmd, sms_fields, *args):
    """ verifies the command and runs it if valid """
    """
    expected_sms_len = ar
    if len(sms_fields) != expected_sms_len:
        return invalid_cmd(sms_fields[0])

    return COMMANDS[cmd](args, sms_fields)
    """


def valid_cmds():
    return '\n'.join(USAGE.values())


def unrecognized_cmd(cmd):
    return respond('The command ' + truncate(cmd, 10) + ' is not'
            + ' recognized. Please try again.',
            'Valid commands are:\n' + valid_cmds())


def check_email(email):
    resp = None
    try:
        validate_email(email)
    except ValidationError:
        resp = 'The email "' + email + '" appears to be invalid.' + ' Please try again.'

    return email, resp


def change_phone_number(from_number, sms_fields):
    expected_sms_len = 4
    if len(sms_fields) != expected_sms_len:
        return invalid_cmd(sms_fields[0])

    email, resp = check_email(sms_fields[1])
    if resp is not None:
        return respond(resp)

    # finish this


def new_user(from_number, sms_fields):
    min_sms_len = 4
    if len(sms_fields) < min_sms_len:
        return invalid_cmd(sms_fields[0])

    email, resp = check_email(sms_fields[1])
    if resp is not None:
        return respond(resp)

    try:
        user = CustomUser.objects.get(email=email)
        user.phone_number = from_number
        user.save()

        return respond('We notice you already have an account with this email.' +
                'Text ' + USAGE['#number'] + ' to update the phone number for this account.')

    except CustomUser.DoesNotExist:
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


def respond(*args):
    r = Response()
    for msg in args:
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


import copy

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User


def debug(request):
    return send_welcome_email(request, u'brian.tubergen@gmail.com')


def send_welcome_email(request, to_email):
    # return HttpResponse(to_email)
    try:
        validate_email(to_email)
    except ValidationError:
        raise
    emails = []
    for u in User.objects.all():
        emails.append(u.email)
    # return HttpResponse(str(emails))
    return HttpResponse(str(User.objects.filter(email__iexact=to_email)))  # , is_active=True)))

    post = copy.copy(request.POST)
    post['email'] = to_email
    form = PasswordResetForm(post)   # {'email': to_email})
    if form.is_valid():
        # return HttpResponse(str(form.is_valid()))
        form.clean_email()
        return HttpResponse(str(form.users_cache))

    opts = {
        'email_template_name': 'registration/welcome_email.html',
        'subject_template_name': 'welcome/welcome_subject.txt',
    }
    # form.save(**opts)
    opts
