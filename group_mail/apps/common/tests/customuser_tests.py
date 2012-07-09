"""
need to unit test deactivate to ensure that we can deactivate multiple accounts
(possible issues with duplicate entry for username = '', etc

        # self.username, self.email, self.phone_number = [None] * 3
"""


from django.db import IntegrityError
from group_mail.apps.common.models import CustomUser, Email
from group_mail.apps.test.test_utils import NoMMTestCase
from group_mail.apps.group.models import Group


class CustomUserTest(NoMMTestCase):
    def setUp(self):
        super(CustomUserTest, self).setUp()
        self.kwargs = {'email': 'myemail@gmail.com',
                'first_name': None,
                'last_name': 'last_name',
                'phone_number': '1234567890'}

    def test_basic_populate(self):
        u = CustomUser.objects.create_user(**self.kwargs)
        fn = 'first'
        u.populate(first_name=fn)
        self.assertEqual(u.first_name, fn, 'first name not properly populated')

    def test_email_populate(self):
        u = CustomUser.objects.create_user(**self.kwargs)
        email = 'something@gmail.com'
        u.populate(email=email)

        self.assertEqual(u.email_set.all()[1].email, email, \
                'email not in email_set; not properly populated')

        user = CustomUser.objects.get(email=email)
        self.assertEqual(user.id, u.id, 'get method returned wrong user')

    def test_double_identical_populate(self):
        u = CustomUser.objects.create_user(**self.kwargs)
        email = 'something@gmail.com'
        u.populate(email=email)
        u.populate(email=email)

        self.assertEqual(u.email_set.all()[1].email, email, \
                'email not in email_set; not properly populated')

    def test_email_populate_when_email_object_already_exists(self):
        u1 = CustomUser.objects.create_user(**self.kwargs)

        email = 'something@gmail.com'
        self.kwargs['email'] = email
        self.kwargs['phone_number'] = self.kwargs['phone_number'][::-1]
        u2 = CustomUser.objects.create_user(**self.kwargs)
        try:
            u1.populate(email)
        except IntegrityError:
            self.assertEqual(len(u1.email_set.all()), 1, \
                    'u1 has wrong email set len')
            self.assertEqual(len(u2.email_set.all()), 1, \
                    'u2 has wrong email set len')

    def test_get_memberships(self):
        u = CustomUser.objects.create_user(**self.kwargs)
        groups = {'g1': {'creator_email': u.email, 'group_name': 'name1', 'group_code': 'code1'},
                'g2': {'creator_email': u.email, 'group_name': 'name2', 'group_code': 'code2'}}

        g1 = Group.objects.create_group(**groups['g1'])
        g2 = Group.objects.create_group(**groups['g2'])

        email_obj = Email.objects.get(user=u)
        self.assertTrue(email_obj in g1.emails.all(), "group 1 is missing the user's email")
        self.assertTrue(email_obj in g2.emails.all(), "group 2 is missing the user's email")

        memberships = u.get_memberships()
        self.assertTrue((g1.id == memberships[0].id) or (g2.id == memberships[0].id), \
                "user is missing a group")
        self.assertTrue((g1.id == memberships[1].id) or (g2.id == memberships[1].id), \
                "user is missing a group")

    def test_remove_nonprimary_email(self):
        """
        Tests that remove_email() properly removes a user's non-primary email.
        """
        another_email = 'another_email@gmail.com'
        u = self.get_user_with_two_emails(another_email)
        u.remove_email(another_email)
        self.after_remove_email_test(u, another_email, self.kwargs['email'])

    def test_remove_primary_email_when_many_emails(self):
        """
        Tests that remove_email() properly reassigns a user's primary email when we remove an
        email from an account where there are other emails.
        """
        another_email = 'another_email@gmail.com'
        u = self.get_user_with_two_emails(another_email)
        u.remove_email(self.kwargs['email'])
        self.after_remove_email_test(u, self.kwargs['email'], another_email)

    def test_remove_primary_email_when_only_email(self):
        """
        Tests that remove_email() properly deactivates a user's account when we remove an
        email from an account where that email was the only email.
        """
        u = CustomUser.objects.create_user(**self.kwargs)
        self.assertEqual(len(u.email_set.all()), 1, 'wrong initial number of emails')
        u.remove_email(self.kwargs['email'])
        self.after_deactivate_test(u)

    def test_deactivate(self):
        """
        Tests that deactivate() properly deactivates a user's account
        """
        u = CustomUser.objects.create_user(**self.kwargs)
        u.deactivate()
        self.after_deactivate_test(u)

    def get_user_with_two_emails(self, another_email):
        """
        Returns a user with two emails. The primary email is the one given by kwargs.
        """
        u = CustomUser.objects.create_user(**self.kwargs)
        self.assertEqual(len(u.email_set.all()), 1, 'wrong initial number of emails')
        u.populate(email=another_email)
        self.assertEqual(len(u.email_set.all()), 2, 'email improperly populated')
        return u

    def after_remove_email_test(self, u, removed_email, remaining_email):
        """
        Common code that tests whether remove_email worked properly.
        """
        # get a fresh user from the db, since the fields may have been changed
        u = CustomUser.objects.get(id=u.id)
        self.assertEqual(len(u.email_set.all()), 1, 'wrong number of emails after remove')
        self.assertEqual(remaining_email, u.email, 'user has wrong email after remove')

        try:
            Email.objects.get(email=removed_email)
        except Email.DoesNotExist:
            self.assertTrue(False, 'email object was improperly deleted')

    def after_deactivate_test(self, u):
        """
        Common code that tests whether account deactivation worked properly.
        """
        # get a fresh user from the db, since the fields may have been changed
        u = CustomUser.objects.get(id=u.id)
        self.assertNotEqual(u.email, self.kwargs['email'], 'email not cleared on deactivated user')
        self.assertNotEqual(u.username, self.kwargs['email'], 'username not cleared on deactivated user')
        self.assertNotEqual(u.phone_number, self.kwargs['phone_number'], 'phone_number not cleared on deactivated user')
        self.assertEqual(u.is_active, False, 'deactivated user not inactive')

        try:
            Email.objects.get(email=self.kwargs['email'])
        except Email.DoesNotExist:
            self.assertTrue(False, 'email object was improperly deleted')

        """
        Currently, a deactivate() doesn't delete the email, so it's not possible to
        create a new user with that email. Thus we comment out the following code:

        u2 = CustomUser.objects.create_user(**self.kwargs)
        self.assertNotEqual(u2.id, u.id, 'new user and deleted user have same id')
        self.assertEqual(u2.email, self.kwargs['email'], 'new user has wrong email')

        email_obj = Email.objects.get(email=self.kwargs['email'])
        self.assertEqual(u2.id, email_obj.user.id, 'email_obj points to wrong user')
        """
