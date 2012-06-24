""" This isn't a real app. The only purpose is to populate the db
    on local development servers. """
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.models import Group
from django.http import HttpResponse


def brian_populate():
    users = [
            {'first_name': 'b', 'last_name': 't', \
                'phone_number': 11, 'email': 'brian.tubergen@gmail.com'},
            {'first_name': 'b', 'last_name': 't', \
                'phone_number': 12, 'email': 'itstubeytime@gmail.com'},
            {'first_name': 'b', 'last_name': 't', \
                'phone_number': 13, 'email': 'listserv.receiver@gmail.com'},
            {'first_name': 'b', 'last_name': 't', \
                'phone_number': 14, 'email': 'group.mail.errors@gmail.com'}
            ]
    emails = []
    for user in users:
        CustomUser.objects.create_user(
                user['email'], 'root', user['first_name'], user['last_name'], \
                user['phone_number'])
        emails.append(user['email'])
    resp = "Created brian's users...<br>"
    resp += '<br>'.join(map(str, list(emails)))
    return resp


def populate(request):
    resp = brian_populate()

    """
    num_users = 10
    num_groups = 10
    password = 'root'

    for i in xrange(0, num_users):
        name = 'user%d' % i
        email = '%s@gmail.com' % name
        phone_number = '111222333%d' % i
        CustomUser.objects.create_user(email, password,
                '%s_first_name' % name, '%s_last_name' % name, phone_number)

    users = CustomUser.objects.all()
    emails = [u.email for u in CustomUser.objects.all()]
    for i in xrange(0, num_groups):
        group_name = 'group%d' % i
        group_code = 'group_code%d' % i
        Group.objects.create_group(emails[i], group_name, group_code)
        # create_group adds email as a member

    groups = Group.objects.all()
    resp += 'Created users...<br>'
    resp += '<br>'.join(map(str, list(users)))
    resp += '<br><br>Each user has password=%s' % password
    resp += '<br><br>Created groups...<br>'
    resp += '<br>'.join(map(str, list(groups)))
    resp += '<br><br>Each group has all users as members.'
    resp += '<br><br>group[i] has user[i] as admin.'
    """
    return HttpResponse(resp)
