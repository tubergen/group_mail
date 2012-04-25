from django.conf.urls import patterns, include, url
from group_mail.apps.sms.views import parse_sms

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    (r'^reply/', parse_sms),

    # Examples:
    # url(r'^$', 'group_mail.views.home', name='home'),
    # url(r'^group_mail/', include('group_mail.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
