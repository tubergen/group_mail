from django.conf import settings
from django.conf.urls import patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from group_mail.apps.sms.views import parse_sms
from group_mail.apps.common.views import homepage_splitter
from group_mail.apps.group.views import group_info
from group_mail.apps.populate_db.views import populate

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    (r'^twilio_reply/$', parse_sms),
    (r'^$', homepage_splitter),
    (r'^group/(?P<group_name>[0-9A-Za-z]+)$', group_info),
    (r'^login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    # Examples:
    # url(r'^$', 'group_mail.views.home', name='home'),
    # url(r'^group_mail/', include('group_mail.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^populate/$', populate),
    )


urlpatterns += patterns('django.contrib.auth.views',
    (r'^password_reset/$', 'password_reset', {}),

    (r'^password_reset/done/$', 'password_reset_done', {}),

    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'password_reset_confirm', {}),
    #    {'post_reset_redirect': 'accounts/login/',
    #     'post_reset_redirect': 'accounts/reset/done/'}),

    (r'^reset/done/$', 'password_reset_complete', {}),
)

urlpatterns += staticfiles_urlpatterns()
