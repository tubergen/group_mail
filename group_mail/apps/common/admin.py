from django.contrib import admin
from group_mail.apps.common.models import CustomUser, Email

admin.site.register(CustomUser)
admin.site.register(Email)
