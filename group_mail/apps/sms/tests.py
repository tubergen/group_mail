""" Run with 'manage.py test'. """
""" These tests test the twilio sms parse/response cmds.
    They don't test the mailman db cmds. """

from django.test import TestCase
from django.test import Client
from django.conf import settings
from group_mail.apps.sms.commands import CreateGroupCmd, JoinGroupCmd, Command, Utilities
from group_mail.apps.common.models import Group, CustomUser


def create_test_user(email, phone_number='0123456789', first_name='john', last_name='smith'):
    return CustomUser.objects.create(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number)


def create_test_group(group_creator, group_name='group', group_code='code'):
    g = Group.objects.create(name=group_name,
                             code=group_code)
    g.admins.add(group_creator)
    g.members.add(group_creator)
    return g


class ParseSMSTest(TestCase):

    def setUp(self):
        self.test_dict = {'From': '1234567890',
                          'Body': '#create name code myemail@gmail.com'}
        settings.DEBUG = True

    def cleanUp(self):
        settings.DEBUG = False

    def test_parse_post(self):
        c = Client()
        response = c.post('/twilio_reply/', self.test_dict)
        self.assertTrue(response.content.find('<Sms>') != -1)

    def test_ignore_if_no_from_field(self):
        c = Client()
        response = c.post('/twilio_reply/', {'Body': 'something'})
        self.assertEqual(response.status_code, 404)

    def test_ignore_if_no_data_field(self):
        c = Client()
        response = c.post('/twilio_reply/', {'From': '1234567890'})
        self.assertEqual(response.status_code, 404)


class _CmdTestCase(TestCase):
    def setUp(self):
        self.old_modify = settings.MODIFY_MAILMAN_DB
        settings.MODIFY_MAILMAN_DB = False

    def tearDown(self):
        settings.MODIFY_MAILMAN_DB = True


class CreateGroupCmdTest(_CmdTestCase):
    def setUp(self):
        super(CreateGroupCmdTest, self).setUp()
        self.sms_fields = ['#create', 'group_name', 'group_code', 'email@gmail.com']
        self.from_number = '0123456789'
        self.cmd = CreateGroupCmd(self.sms_fields[0])

    def test_valid_create_group_cmd(self):
        response = str(self.cmd.execute(self.sms_fields, self.from_number))
        self.assertTrue(response.find('Success') != -1, 'Success response not returned')

        groups = Group.objects.all()
        self.assertTrue(len(groups) == 1, 'Incorrect number of groups after single #create cmd')

        g = groups[0]
        self.assertEqual(g.name, self.sms_fields[1], 'Group has incorrect name')
        self.assertEqual(g.code, self.sms_fields[2], 'Group has incorrect code')

        user = CustomUser.objects.get(email=self.sms_fields[3])
        members = g.members.all()
        self.assertTrue(len(members) == 1, 'Group has incorrect number of members')
        self.assertTrue(members[0].username == user.username, 'Group has incorrect member')

        memberships = user.memberships.all()
        self.assertTrue(len(memberships) == 1, 'User has incorrect number of memberships')
        self.assertTrue(memberships[0].name == g.name, "User's group is incorrect")

    def test_group_name_not_allowed(self):
        self.sms_fields[1] = 'word1 word2'
        response = str(self.cmd.execute(self.sms_fields, self.from_number))

        self.assertTrue((response.find('name') != -1) and (response.find('may only contain') != -1),
                'Group-name-not-allowed response not returned')

        groups = Group.objects.all()
        self.assertTrue(len(groups) == 0, "There exists a group with a name that's not allowed")

    def test_group_code_not_allowed(self):
        self.sms_fields[2] = 'word1 word2'
        response = str(self.cmd.execute(self.sms_fields, self.from_number))

        self.assertTrue((response.find('code') != -1) and (response.find('may only contain') != -1),
                'Group-code-not-allowed response not returned')

        groups = Group.objects.all()
        self.assertTrue(len(groups) == 0, "There exists a group with a code that's not allowed")

    def test_group_name_too_long(self):
        self.sms_fields[1] = ''.join(['*' for i in range(Group.MAX_LEN + 1)])
        response = str(self.cmd.execute(self.sms_fields, self.from_number))

        self.assertTrue((response.find('name') != -1) and (response.find('too long') != -1),
                'Group-name-too-long response not returned')

        groups = Group.objects.all()
        self.assertTrue(len(groups) == 0, "There exists a group with a name that's too long")

    def test_group_code_too_long(self):
        self.sms_fields[2] = ''.join(['*' for i in range(Group.MAX_LEN + 1)])
        response = str(self.cmd.execute(self.sms_fields, self.from_number))

        self.assertTrue((response.find('code') != -1) and (response.find('too long') != -1),
                'Group-code-too-long response not returned')

        groups = Group.objects.all()
        self.assertTrue(len(groups) == 0, "There exists a group with a code that's too long")

    def test_group_already_exists(self):
        self.test_valid_create_group_cmd()  # create a valid user in db
        self.sms_fields[3] = 'a' + self.sms_fields[3]   # new user needs a distinct email
        response = str(self.cmd.execute(self.sms_fields, self.from_number[::-1]))
        print '\n\n'
        print response
        print '\n\n'

        self.assertTrue((response.find('group') != -1) and (response.find('already exists') != -1),
                'Group-already-exists response not returned')

        groups = Group.objects.all()
        self.assertTrue(len(groups) == 1, 'There exists two groups with the same name')


class JoinGroupCmdTest(_CmdTestCase):
    def setUp(self):
        super(JoinGroupCmdTest, self).setUp()
        self.sms_fields = ['#create', 'group_name', 'group_code', 'email@gmail.com']
        self.from_number = '0123456789'

        self.group_creator = create_test_user('creator@gmail.com', phone_number='8888888888')
        self.group = create_test_group(self.group_creator, self.sms_fields[1], self.sms_fields[2])

        self.cmd = JoinGroupCmd(self.sms_fields[0])

    def test_valid_join_group_cmd(self):
        response = str(self.cmd.execute(self.sms_fields, self.from_number))
        self.assertTrue(response.find('Success') != -1, 'Success response not returned')

        user = CustomUser.objects.get(email=self.sms_fields[3])
        members = self.group.members.all()

        # ensure the group has 2 members: the creator and the new joiner
        self.assertTrue(len(members) == 2, 'Group has incorrect number of members')
        self.assertTrue((members[0].username == user.username) or
                (members[1].username == user.username), "Group doesn't have newly joined member")
        self.assertTrue((members[0].username == self.group_creator.username) or
                (members[1].username == self.group_creator.username), "Group doesn't have original creator")

        memberships = user.memberships.all()
        self.assertTrue(len(memberships) == 1, 'User has incorrect number of memberships')
        self.assertTrue(memberships[0].name == self.group.name, "User's group is incorrect")

    def test_group_does_not_exist(self):
        self.sms_fields[1] = 'doesnt_exist'
        response = str(self.cmd.execute(self.sms_fields, self.from_number))
        self.assertTrue((response.find('group') != -1) and (response.find('does not exist') != -1),
                'Group-does-not-exist response not returned')

        user = CustomUser.objects.get(email=self.sms_fields[3])
        members = self.group.members.all()

        # ensure the group has 1 members: the creator
        self.assertTrue(len(members) == 1, 'Group has incorrect number of members')
        self.assertTrue(members[0].username == self.group_creator.username,
                "Group doesn't have original creator")

        # ensure the user isn't in the group
        memberships = user.memberships.all()
        self.assertTrue(len(memberships) == 0, 'User has incorrect number of memberships')

    def test_group_code_incorrect(self):
        self.sms_fields[2] = 'incorrect_code'
        response = str(self.cmd.execute(self.sms_fields, self.from_number))
        self.assertTrue((response.find('code') != -1) and (response.find('not correct') != -1),
                'Incorrect-code response not returned')

        user = CustomUser.objects.get(email=self.sms_fields[3])
        members = self.group.members.all()

        # ensure the group has 1 members: the creator
        self.assertTrue(len(members) == 1, 'Group has incorrect number of members')
        self.assertTrue(members[0].username == self.group_creator.username,
                "Group doesn't have original creator")

        # ensure the user isn't in the group
        memberships = user.memberships.all()
        self.assertTrue(len(memberships) == 0, 'User has incorrect number of memberships')

    def test_already_a_member(self):
        self.cmd.execute(self.sms_fields, self.from_number)
        response = str(self.cmd.execute(self.sms_fields, self.from_number))
        self.assertTrue(response.find('already a member') != -1,
                'Already-a-member response not returned')

        user = CustomUser.objects.get(email=self.sms_fields[3])
        members = self.group.members.all()

        # ensure the group has 2 members (and no more): the creator and the new joiner
        self.assertTrue(len(members) == 2, 'Group has incorrect number of members')
        self.assertTrue((members[0].username == user.username) or
                (members[1].username == user.username), "Group doesn't have newly joined member")
        self.assertTrue((members[0].username == self.group_creator.username) or
                (members[1].username == self.group_creator.username), "Group doesn't have original creator")

        memberships = user.memberships.all()
        self.assertTrue(len(memberships) == 1, 'User has incorrect number of memberships')
        self.assertTrue(memberships[0].name == self.group.name, "User's group is incorrect")


class CommandTest(TestCase):

    def setUp(self):
        self.cmd = Command()


class UtilitiesTest(TestCase):

    def test_truncate(self):
        max_len = 10
        text_len = 2 * max_len
        text = ''.join(['*' for i in range(0, text_len)])

        u = Utilities()

        result = u.truncate(text, max_len, include_ellipses=True)
        self.assertTrue(len(result) == 10, 'Result has incorrect length')
        self.assertEqual(result[(max_len - 3):max_len], '...', "Result doesn't end in ellipses")

        result = u.truncate(text, max_len, include_ellipses=False)
        self.assertTrue(len(result) == 10, 'Result has incorrect length')
        self.assertTrue(result[(max_len - 3):max_len] != '...', "Result ends in ellipses when it shouldn't")
