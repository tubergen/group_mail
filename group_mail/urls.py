from django.conf import settings
from django.conf.urls import patterns, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from group_mail.apps.sms.views import parse_sms
from group_mail.apps.common.views import homepage_splitter, claim_email, email_added, email_removed, claim_email_confirm, claim_email_sent
from group_mail.apps.group.views import group_info, create_group, join_group, action_group
from group_mail.apps.populate_db.views import populate
from group_mail.apps.registration.views import register, register_thanks
from group_mail.apps.registration.djviews import password_reset_confirm
from group_mail.apps.registration.forms import LoginForm
from group_mail.apps.common.custom_user_manager import CustomPasswordResetForm

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    (r'^twilio_reply/$', parse_sms),
    (r'^$', homepage_splitter),
    (r'^group/(?P<group_name>[0-9A-Za-z]+)$', group_info),
    (r'^action/group/$', action_group),
    (r'^create/group/$', create_group),
    (r'^join/group/$', join_group),
    (r'^email/added/(?P<email>.+)$', email_added),
    (r'^email/removed/(?P<email>.+)$', email_removed),
    (r'^register/$', register),
    (r'^register/thanks/$', register_thanks),
    (r'^login/$', 'django.contrib.auth.views.login',  {'authentication_form': LoginForm}),
    (r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    # Examples:
    # url(r'^$', 'group_mail.views.home', name='home'),
    # url(r'^group_mail/', include('group_mail.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^populate/$', populate),
    )

# claim email urls
urlpatterns += patterns('',
    (r'^claim/email/sent/(?P<email>.+)$', claim_email_sent),
    (r'^claim/email/(?P<email>.+)$', claim_email),
    (r'^claim/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)-(?P<email>.+)$',
        claim_email_confirm, {}, "claim_email_confirm"),
)

# reset password urls
urlpatterns += patterns('django.contrib.auth.views',
    (r'^password-reset/$', 'password_reset', {'password_reset_form': CustomPasswordResetForm}),
    (r'^password-reset/done/$', 'password_reset_done', {}),
    (r'^reset/done/$', 'password_reset_complete', {}),
)
urlpatterns += patterns('',
    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        password_reset_confirm, {}, "password_reset_confirm"),
    #    {'post_reset_redirect': 'accounts/login/',
    #     'post_reset_redirect': 'accounts/reset/done/'}),
)

urlpatterns += staticfiles_urlpatterns()
