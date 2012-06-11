from django.test import TestCase
from group_mail.apps.common.models import CustomUser, Email
from group_mail.apps.group.models import Group


class EmailTest(TestCase):
    def setUp(self):
        self.kwargs = {'email': 'myemail@gmail.com',
                'first_name': None,
                'last_name': 'last_name',
                'phone_number': '1234567890'}
        self.u = CustomUser.objects.create_user(**self.kwargs)
        self.email_obj = Email.objects.get(user=self.u)

    def test_unsubscribe_all(self):
        Group.objects.create_group(self.u.email, 'group1', 'code1')
        Group.objects.create_group(self.u.email, 'group2', 'code2')
        self.assertEqual(len(self.email_obj.group_set.all()), 2,
                'email is initially subscribed to incorrect number of groups')

        self.email_obj.unsubscribe_all()
        self.assertEqual(len(self.email_obj.group_set.all()), 0,
                'email should no longer be subscribed to any groups, but it is')
