from django.core.exceptions import ValidationError
from group_mail.apps.test.test_utils import NoMMTestCase
from group_mail.apps.common.models import CustomUser, Email


class GetMethodTest(NoMMTestCase):
    def setUp(self):
        super(GetMethodTest, self).setUp()
        self.kwargs = {'email': 'myemail@gmail.com',
                'first_name': 'first_name',
                'last_name': 'last_name',
                'phone_number': '1234567890'}

    def test_get_method_searches_multiple_emails(self):
        user = CustomUser.objects.create_user(**self.kwargs)
        e1 = 'a@a.com'
        e2 = 'b@b.com'
        Email.objects.create(email=e1, user=user)
        Email.objects.create(email=e2, user=user)

        u1 = CustomUser.objects.get(email=e1)
        u2 = CustomUser.objects.get(email=e2)

        self.assertEqual(user.id, u1.id, 'get method returned wrong user')
        self.assertEqual(user.id, u2.id, 'get method returned wrong user')

    """
    TODO: Write test to ensure that get works with more than one
    constraint, and with those weird django selectors (__icontains etc.).
    """


class CreateUserTest(NoMMTestCase):
    def setUp(self):
        super(CreateUserTest, self).setUp()
        self.kwargs = {'email': 'myemail@gmail.com',
                'first_name': 'first_name',
                'last_name': 'last_name',
                'phone_number': '1234567890'}

    def test_basic_create_user(self):
        u = CustomUser.objects.create_user(**self.kwargs)
        user = CustomUser.objects.all()[0]
        self.assertEqual(u.id, user.id, "returned user isn't the same as db user")

        user_properties = {'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number}

        for key in user_properties.keys():
            self.assertEqual(user_properties[key], self.kwargs[key],
                    'user has incorrect %s' % key)

        # test that the email_set also contains the email
        email_obj = user.email_set.all()[0]
        self.assertEqual(email_obj.email, self.kwargs['email'], \
                "email set doesn't contain email")

    def test_create_user_with_field_unpopulated(self):
        self.kwargs['first_name'] = None
        u = CustomUser.objects.create_user(**self.kwargs)
        user = CustomUser.objects.all()[0]
        self.assertEqual(u.id, user.id, "returned user isn't the same as db user")

        user_properties = {'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number}

        # django models will set first_name to '', so make the corresponding
        # change here
        self.kwargs['first_name'] = ''

        for key in user_properties.keys():
            self.assertEqual(user_properties[key], self.kwargs[key],
                    'user has incorrect %s' % key)

    def test_invalid_email(self):
        self.kwargs['email'] = 'invalid'
        try:
            CustomUser.objects.create_user(**self.kwargs)
            self.assertTrue(False, 'invalid email undetected')
        except ValidationError:
            # we expect and want this exception to be thrown
            pass

    def test_duplicate_phone_number(self):
        CustomUser.objects.create_user(**self.kwargs)

        # change the email so we don't get duplicate email
        self.kwargs['email'] += 'a'
        try:
            CustomUser.objects.create_user(**self.kwargs)
            self.assertTrue(False, 'duplicate phone number undetected')
        except CustomUser.DuplicatePhoneNumber:
            # we expect and want this exception to be thrown
            pass

    def test_duplicate_email(self):
        CustomUser.objects.create_user(**self.kwargs)

        # change the phone number so we don't get duplicate phone number
        self.kwargs['phone_number'] = self.kwargs['phone_number'][::-1]
        try:
            CustomUser.objects.create_user(**self.kwargs)
            self.assertTrue(False, 'duplicate email undetected')
        except CustomUser.DuplicateEmail:
            # we expect and want this exception to be thrown
            pass


class GetOrCreateUserTest(NoMMTestCase):
    def setUp(self):
        super(GetOrCreateUserTest, self).setUp()
        self.kwargs = {'email': 'myemail@gmail.com',
                'phone_number': '1234567890',
                'first_name': None,
                'last_name': None}

    def test_basic_get_or_create(self):
        u = CustomUser.objects.get_or_create_user(**self.kwargs)
        user = CustomUser.objects.all()[0]
        self.assertEqual(u.id, user.id, "returned user isn't the same as db user")

        user_properties = {'email': user.email,
                'phone_number': user.phone_number,
                'first_name': user.first_name,
                'last_name': user.last_name}

        # django models will set 'None' fields to '', so make the corresponding
        # change here
        self.kwargs['first_name'] = ''
        self.kwargs['last_name'] = ''

        for key in user_properties.keys():
            self.assertEqual(user_properties[key], self.kwargs[key],
                    'user has incorrect %s' % key)

        # ensure unpopulated fields are unpopulated
        self.assertEqual(u.id, user.id, "returned user isn't the same as db user")

    def test_user_already_exists(self):
        u1 = CustomUser.objects.get_or_create_user(**self.kwargs)
        u2 = CustomUser.objects.get_or_create_user(**self.kwargs)
        self.assertEqual(u1.id, u2.id, 'different user returned')

    def test_find_and_populate_incomplete_users(self):
        """
        if the user doesn't have the phone number specified, we
        still want to be able to get that incomplete user account.

        further, get_or_create should populate some of its fields
        if the fields are specified.
        """
        # create an incomplete user
        u1 = CustomUser.objects.get_or_create_user(**self.kwargs)

        # get that incomplete user, and populate its first_name field
        self.kwargs['first_name'] = 'first'
        u2 = CustomUser.objects.get_or_create_user(**self.kwargs)

        self.assertEqual(u1.id, u2.id, 'returned wrong user')
        self.assertEqual(u2.first_name, self.kwargs['first_name'], \
                'first_name field incorrectly populated')
        # Note: u1.first_name will still be None here.

    def test_populate_phone_number_on_incomplete_user(self):
        """
        ensure that we populate incomplete users' phone numbers. this
        is a case of the above test, but it's special due to the
        significance of phone numbers in get_or_create_user.
        """
        old_no = self.kwargs['phone_number']
        # create an incomplete user
        self.kwargs['phone_number'] = None
        u1 = CustomUser.objects.get_or_create_user(**self.kwargs)

        # get that incomplete user, and populate its phone_number field
        self.kwargs['phone_number'] = old_no
        u2 = CustomUser.objects.get_or_create_user(**self.kwargs)

        self.assertEqual(u1.id, u2.id, 'returned wrong user')
        self.assertEqual(u2.phone_number, self.kwargs['phone_number'], \
                'phone_number field incorrectly populated')
        # Note: u1.phone_number will still be None here.

    def test_inconsistent_phone_number(self):
        """
        there's an account with the specified email, and it has a phone number
        set, but there's no account with the specified phone number
        """
        CustomUser.objects.get_or_create_user(**self.kwargs)
        self.kwargs['phone_number'] = self.kwargs['phone_number'][::-1]
        try:
            CustomUser.objects.get_or_create_user(**self.kwargs)
            self.assertTrue(False, 'Inconsistent phone number not recognized')
        except CustomUser.InconsistentPhoneNumber:
            # we expect and want this exception to be thrown
            pass

    def test_inconsistent_phone_number_conflicting_accounts(self):
        """
        there's an account with the specified email, and there's an account
        with the specified phone number, and they aren't the same
        """
        # set up users that will cause criteria to be met
        CustomUser.objects.get_or_create_user(**self.kwargs)
        self.kwargs['email'] += 'a'
        self.kwargs['phone_number'] = self.kwargs['phone_number'][::-1]
        CustomUser.objects.get_or_create_user(**self.kwargs)

        # change kwargs one more time to meet the critera
        self.kwargs['phone_number'] = self.kwargs['phone_number'][::-1]
        try:
            CustomUser.objects.get_or_create_user(**self.kwargs)
            self.assertTrue(False, 'Inconsistent phone number not recognized')
        except CustomUser.InconsistentPhoneNumber:
            # we expect and want this exception to be thrown
            pass
