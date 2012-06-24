"""
redirect_list is called in mailman/Mailman/Queue/Switchboard.py
to redirect mailman to the proper group_mail mailing list.
"""

import email
from Mailman.Logging.Syslog import syslog
from django.core.management import setup_environ
from group_mail import settings
setup_environ(settings)

from group_mail.apps.common.models import Email
from group_mail.apps.mailman.mailman_cmds import to_listname, is_internal_listname

TO_HEADER = 'To'
DOMAIN = '@' + settings.EMAIL_DOMAIN


def redirect_list(msg, data):
    """
    Redirects the msg and rewrites the data if this a message
    to one of our mailing lists.

    In particular, we manipulate data['listname'] and the msg
    To header to deal with internal/external listnames.
    """
    syslog('debug', 'in the redirect_list function')
    if _sent_to_mailing_list(msg):
        sender = msg.get_sender()
        try:
            listname = data['listname']
        except KeyError:
            syslog('error', 'no listname key in message data')
            return

        syslog('debug', 'listname: %s', listname)

        real_listname = _get_real_listname(sender, listname)
        syslog('debug', 'real_listname: %s', str(real_listname))
        if real_listname:
            error = _replace_header(msg, TO_HEADER, real_listname)
            if error:
                syslog('error', error)
                return
            data['listname'] = real_listname
    else:
        syslog('debug', "email wasn't sent to mailing list")


def _sent_to_mailing_list(msg):
    """
    Returns True if msg was sent to a mailing list,
    i.e. sent to an email that ends with our site's domain.
    """
    fieldvals = msg.get_all(TO_HEADER)
    for name, addr in email.utils.getaddresses(fieldvals):
        syslog('debug', 'addr: %s', addr)
        if addr.find(DOMAIN) != -1:
            return True
    return False


def _replace_header(msg, header, real_listname):
    try:
        msg.replace_header(header, real_listname + DOMAIN)
        return None
    except KeyError:
        return 'no %s header in msg' % header


def _get_real_listname(sender_email, listname):
    """
    Returns the 'real' name of listname.

    For external names, this function returns the internal name.
        e.g. listname = group@tmail.com ==> return _4839@tmail.com

    For internal names, this function returns the external name.
        e.g. listname = _4839@tmail.com ==> return group@tmail.com
    """
    if is_internal_listname(listname):
        name = _get_group_name_from_internal_name(listname)
    else:
        # listname is the name of the relevant group
        name = _get_internal_name_from_group_name(sender_email, listname)
    return name


def _get_group_name_from_internal_name(internal_name):
    """
    Returns the external name of the list whose group id is given by
    internal_name, since internal name takes the form _id.
    """
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
    from group_mail.apps.group.models import Group
    syslog('debug', 'attempting to get internal name')
    try:
        email_obj = Email.objects.get(email=sender_email)
    except Email.DoesNotExist:
        syslog('error', "email object didn't exist: %s " % sender_email)
        return None

    group = Group.objects.get_group_for_email([email_obj], group_name)
    if not group:
        # we didn't find a single group with the listname for this sender
        syslog('error', "group object didn't exist")

    return to_listname(group)
