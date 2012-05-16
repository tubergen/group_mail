""" This isn't a real app. The only purpose is to populate the db
    on local development servers. """
from group_mail.apps.common.models import Group, CustomUser
from django.http import HttpResponse


def populate(request):
    num_users = 10
    num_groups = 10
    password = 'root'

    for i in xrange(0, num_users):
        name = 'user%d' % i
        email = '%s@gmail.com' % name
        # phone_number = '703555333%d' % i
        CustomUser.objects.create_user(email, email, password)

    users = CustomUser.objects.all()
    for i in xrange(0, num_groups):
        group_name = 'group%d' % i
        group_code = 'group_code%d' % i
        group = Group.objects.create(name=group_name,
                                     code=group_code)
        group.members.add(*users)
        group.admins.add(users[i])

    groups = Group.objects.all()
    resp = 'Created users...<br>'
    resp += '<br>'.join(map(str, list(users)))
    resp += '<br><br>Each user has password=%s' % password
    resp += '<br><br>Created groups...<br>'
    resp += '<br>'.join(map(str, list(groups)))
    resp += '<br><br>Each group has all users as members.'
    resp += '<br><br>group[i] has user[i] as admin.'
    return HttpResponse(resp)
