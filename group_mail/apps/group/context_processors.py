from group_mail.apps.group.forms import CreateGroupNavbarForm


def create_group_navbar_form(request):
    if request.user.is_authenticated():
        return {'create_group_navbar_form': CreateGroupNavbarForm()}
    else:
        return {}
