from django.test import TestCase
from django.conf import settings


class NoMMTestCase(TestCase):
    """
    Test cases that disable mailman db modification.
    """
    def setUp(self):
        self.old_modify = settings.MODIFY_MAILMAN_DB
        settings.MODIFY_MAILMAN_DB = False

    def tearDown(self):
        settings.MODIFY_MAILMAN_DB = self.old_modify
