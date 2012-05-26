from django.http import Http404
from django_twilio.decorators import twilio_view
from group_mail.apps.sms.commands import Command, CreateGroupCmd, JoinGroupCmd

COMMAND_CLASSES = {'#create': CreateGroupCmd, '#join': JoinGroupCmd}


@twilio_view
def parse_sms(request):
    from_number = request.GET.get('From', '')
    sms_data = request.GET.get('Body', '')
    if from_number != '' and sms_data != '':
        sms_fields = sms_data.split()
        cmd = COMMAND_CLASSES.get(sms_fields[0], Command)(sms_fields[0])
        return cmd.execute(sms_fields, from_number)

    raise Http404
