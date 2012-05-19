from django.shortcuts import render_to_response
from django.template import RequestContext
from group_mail.apps.common.models import Group, CustomUser
from django.http import HttpResponseRedirect
from group_mail.apps.group.forms import CreateGroupForm
from django.contrib.auth.decorators import login_required


@login_required
def group_info(request, group_name):
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return HttpResponseRedirect('/')

    if request.user not in group.members.all():
        return HttpResponseRedirect('/')

    errors = []
    if request.method == 'POST':
        if not request.POST.get('removed_members'):
            errors.append('No members were selected to be removed.')
        """
        # unclear whether we want to restrict user removal to admins
        if not request.user in group.admins.all():
            errors.append('Must be a group admin to remove members.')
        """
        if not errors:
            for member_email in request.POST.getlist('removed_members'):
                try:
                    user = CustomUser.objects.get(email=member_email)
                except CustomUser.DoesNotExist:
                    user = None
                group.remove_member(user)

            return render_to_response('group/member_removed.html',
                    {'group': group,
                    'member': user,
                    'errors': errors},
                    context_instance=RequestContext(request))

    return render_to_response('group/info.html',
            {'group': group,
            'errors': errors},
            context_instance=RequestContext(request))


@login_required
def create_group(request):
    if request.method == 'POST':
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']
            # no need to except here, since clean_ methods should validate data
            Group.objects.create_group(request.user, group_name,
                    form.cleaned_data['group_code'])
            return HttpResponseRedirect('/group/%s' % group_name)
    else:
        form = CreateGroupForm()

    return render_to_response('group/create.html',
                              {'create_group_form': form},
                              RequestContext(request))
