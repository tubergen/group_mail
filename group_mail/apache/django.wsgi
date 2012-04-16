import os
import sys

path = '/home/ubuntu/djcode/group_mail'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'group_mail.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()