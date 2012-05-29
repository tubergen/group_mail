from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


def homepage_splitter(request):
    if request.user.is_authenticated():
        return logged_in_homepage(request)
    else:
        return landing_page(request)


def landing_page(request):
    return TemplateView.as_view(template_name='landing.html')(request)


@login_required
def logged_in_homepage(request):
    groups_by_email = request.user.get_groups_by_email()
    return render_to_response('group/list.html',
            {'groups_by_email': groups_by_email},
            context_instance=RequestContext(request))
"""
class UserHomeView(DetailView):

    context_object_name = "user"
    model = CustomUser

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PublisherDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['group_list'] = Book.objects.all()
        return context
"""
