from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView


def homepage_splitter(request):
    if request.user.is_authenticated():
        return logged_in_homepage(request)
    else:
        return landing_page(request)


def landing_page(request):
    return TemplateView.as_view(template_name='landing.html')(request)


@login_required
def logged_in_homepage(request):
    groups = request.user.memberships.all()
    return ListView.as_view(
            template_name='group/list.html',
            queryset=groups,
            context_object_name="group_list")(request)
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
