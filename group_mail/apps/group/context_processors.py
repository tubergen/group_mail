from group_mail.apps.common.constants import TYPE_CREATE, TYPE_JOIN
from group_mail.apps.group.forms import GroupNavbarForm


def group_navbar_form(request):
    if request.user.is_authenticated():
        return {'group_navbar_form':
                GroupNavbarForm(request.user),
                'type_create': TYPE_CREATE,
                'type_join': TYPE_JOIN}
    else:
        return {}
