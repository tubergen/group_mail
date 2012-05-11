from django.conf.urls import patterns
from group_mail.apps.sms.views import parse_sms, debug

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    (r'^twilio_reply/', parse_sms),
    (r'^debug2/', debug),

    # Examples:
    # url(r'^$', 'group_mail.views.home', name='home'),
    # url(r'^group_mail/', include('group_mail.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

#django.contrib.auth.views
urlpatterns += patterns('django.contrib.auth.views',
    (r'^password_reset/$', 'password_reset', {}),

    (r'^password_reset/done/$', 'password_reset_done', {}),

    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'password_reset_confirm', {}),
    #    {'post_reset_redirect': 'accounts/login/',
    #     'post_reset_redirect': 'accounts/reset/done/'}),

    (r'^reset/done/$', 'password_reset_complete', {}),
)

urlpatterns += patterns('group_mail.apps.sms.welcome',
    (r'^debug/', 'debug', {}),
)
