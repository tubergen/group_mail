#### As of 5/17, newlist may not work. It's untested since we changed the error
#### surfacing mechanism

""" Provides wrappers for the necessary mailman commands. """

import sys
import subprocess
import MySQLdb
from django.conf import settings

##########################################################################
"""All of the following functions return a list of errors as strings."""


def newlist(list_name, owner_email, list_password):
    args = [_get_script_dir('newlist'), list_name, owner_email, list_password]
    errors = _exec_cmd(*args, stdin_hook='\n')
    if not errors:
        # mailman doesn't automatically add the list creator as a member, but
        # we want to
        errors = add_members(list_name, owner_email)
        if not errors:
            add_postfix_mysql_alias(list_name)
    else:
        raise MailmanError(errors)


def remove_members(list_name, members):
    """
    members should be a single string or a list of strings, where each string is
    a members' email which will be removed from list_name.
    """
    members = list(members)  # in case members is a single string
    args = ['remove_members', list_name] + members
    return _exec_cmd(*args)


def add_members(list_name, members):
    """
    members should be a newline-delimited string of emails to add to
    list_name. e.g.: 'brian@gmail.com\nellie@gmail.com\nanne@gmail.com'
    """
    args = [_get_script_dir('add_members'), '-r', '-', list_name]
    return _exec_cmd(*args, stdin_hook=members)


def dumpdb(list_name):
    """
    this will throw an IOError if the list doesn't exist. Not robust enough
    for use in production.
    """
    args = [_get_script_dir('dumpdb'), _get_list_dir(list_name) + '/config.pck']
    return _exec_cmd(*args)


def rmlist(list_name):
    args = [_get_script_dir('rmlist'), '-a', _get_list_dir(list_name)]
    return _exec_cmd(*args)

##########################################################################


class MailmanError(Exception):
    """ Generic Mailman Error """
    def __init__(self, errors=None):
        if not errors:
            msg = 'Error with mailman command.'
        else:
            msg = '\n'.join(errors)
        super(MailmanError, self).__init__(msg)

    def __str__(self):
        return repr(self.msg)

##########################################################################
""" Private helper functions """

MAILMAN_ERRORS = ['No such member', 'Already a member',
                  'Bad/Invalid email address', 'Illegal list name',
                  'List already exists', 'No such list',
                  'sudo'  # catch sudo (permission) errors
                  ]

ROOT_MAILMAN_DIR = '/var/lib/mailman'


def _get_script_dir(script_name):
    return ROOT_MAILMAN_DIR + '/bin/' + script_name


def _get_list_dir(list_name):
    return ROOT_MAILMAN_DIR + '/lists/' + list_name


def _get_errors(result):
    """
    returns a list of errors specified in the tuple result, which is
    presumed to be of the form (sysout, syserr)
    """
    errors = []
    output = result[0] + result[1]

    # we assume each error appears on its own line
    lines = output.split('\n')
    for line in lines:
        for err in MAILMAN_ERRORS:
            if line.find(err) != -1:
                errors.append(line)

    print >>sys.stderr, errors
    return errors


def _exec_cmd(*args, **kwargs):
    """"
    args[0] should be a string giving the command to be executed.
    args[1:] should be strings, where each string is an argument to the command.
    kwargs['stdin_hook'] is optional; if set, the value will be sent to the
    process executing the command on stdin.
    """
    try:
        args = list(args)
        if args[0] != 'sudo':
            args.insert(0, 'sudo')
        PIPE = subprocess.PIPE

        if 'stdin_hook' in kwargs:
            p = subprocess.Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        else:
            p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)

        result = p.communicate(kwargs.get('stdin_hook'))

        print >>sys.stderr, '---sysout---\n' + result[0]
        print >>sys.stderr, '---syserr---\n' + result[1]
        return _get_errors(result)
    except OSError, e:
        print >>sys.stderr, 'Execution failed: ', e
        return [e]


def add_postfix_mysql_alias(list_name):
    """ We have to add an alias to the postfix mysql db which maps
        list_name@domain.com to list_Name@lists.domain.com to make mailman
        and postfix cooperate. """

    domain = settings.EMAIL_DOMAIN
    sql_args = {'from_list': list_name + '@' + domain,
                'to_list':  list_name + '@lists.' + domain}

    db = MySQLdb.connect(host='localhost', user='root', passwd='root',
            db='maildb')
    cursor = db.cursor()

    sql = "INSERT INTO aliases (mail, destination) VALUES (%(from_list)s, %(to_list)s)"
    cursor.execute(sql, sql_args)

    cursor.close()
    db.commit()
    db.close()
##########################################################################


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'add':
        add_members('alist', 'brian.tubergengmail.com\ntubergen@princeton.edu')
    elif len(sys.argv) > 1 and sys.argv[1] == 'new':
        newlist('alist', 'tubergen@princeton.edu', 'hack')
    elif len(sys.argv) > 1 and sys.argv[1] == 'rem':
        remove_members('alist', ['brian.tubergen@gmail.com',
                                 'tubergen@princeton.edu'])
    elif len(sys.argv) > 1 and sys.argv[1] == 'dump':
        dumpdb('alist')
    elif len(sys.argv) > 1 and sys.argv[1] == 'rmlist':
        rmlist('alist')

if __name__ == '__main__':
    main()
