#### As of 5/17, newlist may not work. It's untested since we changed the error
#### surfacing mechanism
### 5/21 note: this may apply to all commands.

""" Provides wrappers for the necessary mailman commands. """

import sys
import subprocess
import MySQLdb
from django.conf import settings

INTERNAL_LISTNAME_PREFIX = '_'


def to_listname(group):
    # internal, private listnames will start with _
    name = '%c%d' % (INTERNAL_LISTNAME_PREFIX, group.id)
    return name


def is_internal_listname(listname):
    return listname[0] == INTERNAL_LISTNAME_PREFIX


def first_newlist(group, owner_email, list_password):
    # if there are no other groups with group.name, we need to create both
    # group.name@tmail.com and g-group.id@tmail.com in mailman
    # owner_email should be something internal, but for debugging we leave it
    # external
    try:
        newlist(group, owner_email, list_password, group.name, add_creator=False)
        # the second add_creator is false, since we'll add the creator in
        # the group.add_members call
        newlist(group, owner_email, list_password, add_creator=False)
    except MailmanError:
        raise


# all this if not listname junk is a temporary hack
def newlist(group, owner_email, list_password, listname=None, add_creator=True):
    if not listname:
        listname = to_listname(group)
    args = [_get_script_dir('newlist'), listname, owner_email, list_password]
    errors = _exec_cmd(*args, stdin_hook='\n')
    if not errors:
        # mailman doesn't automatically add the list creator as a member, but
        # we want to
        if add_creator:
            errors = add_members(group, owner_email)
        if not errors:
            add_postfix_mysql_alias(listname)
    else:
        raise MailmanError(errors)


def remove_members(group, members):
    """
    members should be a single string or a list of strings, where each string is
    a members' email which will be removed from listname.
    """
    listname = to_listname(group)
    members = list(members)  # in case members is a single string
    args = ['remove_members', listname] + members
    errors = _exec_cmd(*args)
    if errors:
        raise MailmanError(errors)


def add_members(group, members):
    """
    members should be a list or newline-delimited string of emails to add
    to listname. e.g.: 'brian@gmail.com\nellie@gmail.com\nanne@gmail.com'
    """
    listname = to_listname(group)
    if isinstance(members, list):
        members = '\n'.join(members)
    elif not isinstance(members, basestring):
        raise TypeError('members must be a list or string')

    args = [_get_script_dir('add_members'), '-r', '-', listname]
    errors = _exec_cmd(*args, stdin_hook=members)
    if errors:
        raise MailmanError(errors)


def dumpdb(group):
    """
    this will throw an IOError if the list doesn't exist. Not robust enough
    for use in production.
    """
    listname = to_listname(group)
    args = [_get_script_dir('dumpdb'), _get_list_dir(listname) + '/config.pck']
    errors = _exec_cmd(*args)
    if errors:
        raise MailmanError(errors)


def rmlist(group):
    listname = to_listname(group)
    args = [_get_script_dir('rmlist'), '-a', _get_list_dir(listname)]
    errors = _exec_cmd(*args)
    if errors:
        raise MailmanError(errors)


class MailmanError(Exception):
    """ Generic Mailman Error """
    def __init__(self, errors=None):
        if not errors:
            self.msg = 'Error with mailman command.'
        else:
            self.msg = '\n'.join(errors)
        super(MailmanError, self).__init__(self.msg)

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


def _get_list_dir(listname):
    return ROOT_MAILMAN_DIR + '/lists/' + listname


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
    except OSError:  # , e:
        raise
        # print >>sys.stderr, 'Execution failed: ', e
        # return [e]


def add_postfix_mysql_alias(listname):
    """
    We have to add an alias to the postfix mysql db which maps
    listname@domain.com to list_Name@lists.domain.com to make mailman
    and postfix cooperate.
    """
    domain = settings.EMAIL_DOMAIN
    sql_args = {'from_list': listname + '@' + domain,
                'to_list':  listname + '@lists.' + domain}

    db = MySQLdb.connect(host='localhost', user='root', passwd='root',
            db='maildb')
    cursor = db.cursor()

    sql = "INSERT INTO aliases (mail, destination) VALUES (%(from_list)s, %(to_list)s)"
    cursor.execute(sql, sql_args)

    cursor.close()
    db.commit()
    db.close()
##########################################################################


class TestGroup():
    def __init__(self, id=1):
        self.id = id
        self.name = 'mygroup%d' % id
        print 'True group name : %s' % self.name


def main():
    if len(sys.argv) > 2:
        id = int(sys.argv[2])
    group = TestGroup(id)
    if len(sys.argv) > 1 and sys.argv[1] == 'add':
        add_members(group, 'brian.tubergengmail.com\ntubergen@princeton.edu')
    elif len(sys.argv) > 1 and sys.argv[1] == 'new':
        first_newlist(group, 'brian.tubergen@gmail.com', 'hack')
    elif len(sys.argv) > 1 and sys.argv[1] == 'rem':
        remove_members(group, ['brian.tubergen@gmail.com',
                                 'tubergen@princeton.edu'])
    elif len(sys.argv) > 1 and sys.argv[1] == 'dump':
        dumpdb(group)
    elif len(sys.argv) > 1 and sys.argv[1] == 'rmlist':
        rmlist(group)

if __name__ == '__main__':
    main()
