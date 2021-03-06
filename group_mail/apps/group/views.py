from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from group_mail.apps.common.constants import TYPE_CREATE, TYPE_JOIN
from group_mail.apps.group.models import Group
from group_mail.apps.common.models import CustomUser
from group_mail.apps.group.forms import CreateGroupForm, JoinGroupForm, AddMembersForm


@login_required
def group_info(request, group_name):
    group = Group.objects.get_group_for_email(request.user.email_set.all(), group_name)
    if group is None:
        return HttpResponseRedirect('/')

    errors = []
    add_members_form = AddMembersForm()
    if request.method == 'POST':
        if request.POST.get('remove_members_submit'):
            if not request.POST.get('removed_members'):
                errors.append('No members were selected to be removed.')
            """
            # unclear whether we want to restrict user removal to admins
            if not request.user in group.admins.all():
                errors.append('Must be a group admin to remove members.')
            """
            if not errors:
                removed_member_emails = request.POST.getlist('removed_members')
                group.remove_members(removed_member_emails)

                return render_to_response('group/member_removed.html',
                        {'group': group,
                        'removed_member_emails': removed_member_emails},
                        context_instance=RequestContext(request))
        elif request.POST.get('add_members_submit'):
            add_members_form = AddMembersForm(request.POST)
            if add_members_form.is_valid():
                added_member_emails = add_members_form.cleaned_data['emails']
                group.add_members(added_member_emails)
                return render_to_response('group/member_added.html',
                        {'group': group,
                        'added_member_emails': added_member_emails,
                        'errors': errors},
                        context_instance=RequestContext(request))

    return render_to_response('group/info.html',
            {'group': group,
            'errors': errors,
            'add_members_form': add_members_form},
            context_instance=RequestContext(request))


def get_initial(request):
    """
    Returns the initial values dict for a create group form or a join group
    form if they appear in request.GET.
    """
    if request.method == 'GET':
        return {'group_name': request.GET.get('group_name', ''),
                'group_code': request.GET.get('group_code', ''),
                'email': request.GET.get('email', '')}


@login_required
def create_group(request):
    if request.method == 'POST':
        form = CreateGroupForm(request.user, request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']
            creator_email = form.cleaned_data['email']
            # no need to except here, since clean_ methods should validate data
            Group.objects.create_group(creator_email, group_name,
                    form.cleaned_data['group_code'])
            return HttpResponseRedirect('/group/%s' % group_name)
    else:
        form = CreateGroupForm(request.user, initial=get_initial(request))

    return render_to_response('group/create_or_join.html',
                              {'form': form,
                               'type': TYPE_CREATE},
                              RequestContext(request))


@login_required
def join_group(request):
    if request.method == 'POST':
        form = JoinGroupForm(request.user, request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']
            group_code = form.cleaned_data['group_code']
            email = form.cleaned_data['email']
            group = Group.objects.get(name=group_name, code=group_code)
            try:
                group.add_members([email])
            except CustomUser.AlreadyMember:
                pass
            return HttpResponseRedirect('/group/%s' % group_name)
    else:
        form = JoinGroupForm(request.user, initial=get_initial(request))

    return render_to_response('group/create_or_join.html',
                              {'form': form,
                               'type': TYPE_JOIN},
                              RequestContext(request))


def action_group(request):
    if request.method == 'POST' and 'submit' in request.POST:
        if request.POST['submit'] == TYPE_CREATE:
            return create_group(request)
        elif request.POST['submit'] == TYPE_JOIN:
            return join_group(request)
