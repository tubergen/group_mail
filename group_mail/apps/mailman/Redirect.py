from Mailman.Logging.Syslog import syslog

from django.conf import settings
settings.configure(
    DATABASE_ENGINE='django.db.backends.mysql',
    DATABASE_NAME='group_mail_db',
    DATABASE_USER='root',
    DATABASE_PASSWORD='root',
    DATABASE_HOST='localhost',
    DATABASE_PORT='',
    TIME_ZONE='America/New_York',
)
import sys
print sys.path
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.models import Group
from group_mail.apps.mailman.mailman_cmds import to_listname


def redirect_list(msg, data):
    sender = msg.get_sender()
    try:
        listname = data['listname']
    except KeyError:
        syslog('error', 'no listname key in message data')
        return

    syslog('debug', 'listname: %s', listname)

    real_listname = _get_real_listname(sender, listname)
    if real_listname:
        syslog('debug', 'real_listname: %s', real_listname)
        try:
            msg.replace_header('To', real_listname + '@briantubergen.com')
        except KeyError:
            syslog('error', 'no To header in msg')
            return
        data['listname'] = real_listname


def _get_real_listname(sender, listname):
    try:
        user = CustomUser.objects.get(email=sender)
    except CustomUser.DoesNotExist:
        syslog('error', "custom user object didn't exist")
        return None
    try:
        group = user.memberships.get(name=listname)
        return to_listname(group)
    except Group.DoesNotExist:
        syslog('error', "group object didn't exist")
        return None
