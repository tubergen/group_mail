from django.core.exceptions import ValidationError
from django.test import TestCase
from group_mail.apps.common.models import CustomUser


class CreateUserTest(TestCase):
    def setUp(self):
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
        try:
            CustomUser.objects.create_user(**self.kwargs)
            self.assertTrue(False, 'duplicate phone number undetected')
        except CustomUser.DuplicatePhoneNumber:
            # we expect and want this exception to be thrown
            pass

    def test_duplicate_email(self):
        CustomUser.objects.create_user(**self.kwargs)
        try:
            # change the phone number so we don't get duplicate phone number
            self.kwargs['phone_number'] = self.kwargs['phone_number'][::-1]
            CustomUser.objects.create_user(**self.kwargs)
            self.assertTrue(False, 'duplicate email undetected')
        except CustomUser.DuplicateEmail:
            # we expect and want this exception to be thrown
            pass


class GetOrCreateUserTest(TestCase):

    def setUp(self):
        self.kwargs = {'email': 'myemail@gmail.com',
                'phone_number': '1234567890'}

    def test_basic_get_or_create(self):
        u = CustomUser.objects.get_or_create_user(**self.kwargs)
        user = CustomUser.objects.all()[0]
        self.assertEqual(u.id, user.id, "returned user isn't the same as db user")

        user_properties = {'email': user.email,
                'phone_number': user.phone_number}

        for key in user_properties.keys():
            self.assertEqual(user_properties[key], self.kwargs[key],
                    'user has incorrect %s' % key)

    def test_user_already_exists(self):
        u1 = CustomUser.objects.get_or_create_user(**self.kwargs)
        u2 = CustomUser.objects.get_or_create_user(**self.kwargs)
        self.assertEqual(u1.id, u2.id, 'different user returned')

    def test_inconsistent_phone_number(self):
        CustomUser.objects.get_or_create_user(**self.kwargs)
        try:
            self.kwargs['phone_number'] = self.kwargs['phone_number'][::-1]
            CustomUser.objects.get_or_create_user(**self.kwargs)
            self.assertTrue(False, 'Inconsistent phone number not recognized')
        except CustomUser.InconsistentPhoneNumber:
            # we expect and want this exception to be thrown
            pass
