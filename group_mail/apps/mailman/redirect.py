"""
redirect_list is called in mailman/Mailman/Queue/Switchboard.py
to redirect mailman to the proper group_mail mailing list.
"""

from Mailman.Logging.Syslog import syslog
from django.core.management import setup_environ
from group_mail import settings
setup_environ(settings)

"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'group_mail.settings'
"""

"""
from django.conf import settings
settings.configure(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2',
            'NAME': 'group_mail_db',                      # Or path to database
            'USER': 'root',                      # Not used with sqlite3.
            'PASSWORD': 'root',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost
            'PORT': '',                      # Set to empty string for default.
        }
    }
)
"""

"""
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
"""
from group_mail.apps.common.models import Email
from group_mail.apps.mailman.mailman_cmds import to_listname, is_internal_listname


def redirect_list(msg, data):
    syslog('debug', 'in the redirect_list function')
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


def _get_real_listname(sender_email, listname):
    """
    Returns the 'real' name of listname.

    For external names, this function returns the internal name.
        e.g. listname = group@tmail.com ==> return _4839@tmail.com

    For internal names, this function returns the external name.
        e.g. listname = _4839@tmail.com ==> return group@tmail.com
    """
    if is_internal_listname(listname):
        return _get_group_name_from_internal_name(listname)
    else:
        # listname is the name of the relevant group
        return _get_internal_name_from_group_name(sender_email, listname)


def _get_group_name_from_internal_name(internal_name):
    from group_mail.apps.group.models import Group
    group_id = internal_name[1:]
    try:
        return Group.objects.get(id=group_id).name
    except Group.DoesNotExist:
        syslog('error', "group object didn't exist")
        return None


def _get_internal_name_from_group_name(sender_email, group_name):
    """
    Returns the internal name of the list which is associated with group_name
    and to which sender_email is subscribed.
    """
    try:
        email_obj = Email.objects.get(email=sender_email)
    except Email.DoesNotExist:
        syslog('error', "email object didn't exist: %s " % sender_email)
        return None

    for group in email_obj.group_set.all():
        if group.name == group_name:
            return to_listname(group)

    # we didn't find a single group with the listname for this sender
    syslog('error', "group object didn't exist")
    return None
