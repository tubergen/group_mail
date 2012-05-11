from django.contrib.sites.models import Site
from django.core.management.base import NoArgsCommand
from optparse import make_option


class Command(NoArgsCommand):

    help = "Sets the sitename database entry to briantubergen.com."

    option_list = NoArgsCommand.option_list + (
        make_option('--verbose', action='store_true'),
    )

    def handle_noargs(self, **options):
        my_site = Site.objects.get(pk=1)
        domain = 'briantubergen.com'
        my_site.domain = domain
        my_site.name = domain
        my_site.save()
