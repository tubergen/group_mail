from django.utils.safestring import mark_safe
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from group_mail.apps.common.errors import CustomException
from group_mail.apps.common.custom_user_manager import CustomUserManager


class CustomUser(User):
    MAX_LEN = 128  # max length of email, password
    phone_number = models.CharField(max_length=20, blank=True)

    objects = CustomUserManager()

    def is_complete(self):
        """ returns true if the CustomUser has a complete account
            (all #user cmd info populated) and false otherwise """
        if self.first_name and self.last_name and self.phone_number:
            return True
        else:
            return False

    def populate(self, email=None, first_name=None, last_name=None, phone_number=None):
        if email:
            # check if this account already has the email
            try:
                found_email = self.email_set.get(email=email)
            except Email.DoesNotExist:
                found_email = None

            if not found_email:
                # This will raise an IntegrityError if the email object already exists
                Email.objects.create(email=email, user=self)

        if first_name and not self.first_name:
            self.first_name = first_name
        if last_name and not self.last_name:
            self.last_name = last_name
        if phone_number and not self.phone_number:
            self.phone_number = phone_number
        self.save()

    def get_memberships(self):
        memberships = []
        for group_list in self.get_groups_by_email().values():
            for group in group_list:
                memberships.append(group)
        return memberships

    def get_groups_by_email(self):
        """
        Returns a dict of the form:
        {email1: [group1_1, group2_1, ...],
        email2: [group1_2, group2_2, ...],
        ...
        }
        This is a dictionary where each of the user's emails is a key,
        associated with a value which is a list of groups to which that email
        is subscribed.
        """
        result = {}
        for email in self.email_set.all():
            result[email] = email.group_set.all()
        return result

    def deactivate(self):
        """
        Deactivates account by freeing up unique fields and setting account
        to be inactive.
        """
        try:
            email_obj = Email.objects.get(email=self.email)
            email_obj.delete()
        except Email.DoesNotExist:
            # that's fine; the email obj is already deleted
            pass
        self.username, self.email, self.phone_number = [''] * 3
        self.is_active = False
        self.save()

    def remove_email(self, email, unsubscribe=False):
        """
        Removes the email from the user's account. If unsubscribe is True,
        we also remove the email from any groups and mailman mailing lists that
        it's associated with.
        """
        try:
            email_obj = Email.objects.get(email=email)
        except Email.DoesNotExist:
            raise

        if unsubscribe:
            email_obj.unsubscribe_all()
        email_obj.delete()

        if self.email == email:
            # if we've removed the primary email, we need to change the primary
            # email and the username
            my_emails = self.email_set.all()
            if len(my_emails) != 0:
                self.email = my_emails[0].email
                self.username = my_emails[0].email
                self.save()
            else:
                # there are no other emails for this account, so deactivate it
                self.deactivate()

    def has_email(self, email):
        email_obj = Email.objects.get(email=email)
        if email_obj in self.email_set.all():
            return True
        else:
            return False

    """ Custom Exceptions """

    class _DuplicateField(CustomException):
        def __init__(self, msg=None, field='field unspecified', value=''):
            if msg is None:
                msg = 'An account with the %s %s already exists.' % (field, value)
            super(CustomUser._DuplicateField, self).__init__(msg)

    class DuplicatePhoneNumber(_DuplicateField):
        def __init__(self, msg=None, phone_number=''):
            super(CustomUser.DuplicatePhoneNumber, self).__init__(msg, 'phone number', phone_number)

    class DuplicateEmail(_DuplicateField):
        @classmethod
        def claim_link_error_msg(class_, email):
            return mark_safe('The email already belongs to an account.'
                    ' Please click %s' % class_.claim_email_link_html(email) + \
                    ' if the email belongs to you.')

        @staticmethod
        def claim_email_link_html(email):
            from group_mail.apps.common.views import claim_email
            claim_url = reverse(claim_email, kwargs={'email': email})
            return '<a href="%s">here</a>' % claim_url

        def __init__(self, msg=None, email='', include_claim_link=False):
            if include_claim_link:
                msg = self.claim_link_error_msg(email)
            super(CustomUser.DuplicateEmail, self).__init__(msg, 'email', email)

    class AlreadyMember(CustomException):
        def __init__(self, msg=None, email='', group_name=''):
            if msg is None:
                msg = 'The member %s is already a member of the group %s' % \
                        (email, group_name)
            super(CustomUser.AlreadyMember, self).__init__(msg)

    class InconsistentPhoneNumber(CustomException):
        def __init__(self, msg=None, email=''):
            if msg is None:
                msg = 'The email %s is associated with a different phone number.' % \
                        email
            super(CustomUser.InconsistentPhoneNumber, self).__init__(msg)


class Email(models.Model):
    email = models.EmailField(unique=True)
    user = models.ForeignKey(CustomUser, related_name='email_set')

    def unsubscribe_all(self):
        """
        Unsubscribes Email from all groups to which it's subscribed.

        What should happen when the user unsubscribes from a group that
        he's admin of? Right now, we do nothing: he remains admin, even
        though he can't even access the group.
        """
        for group in self.group_set.all():
            group.remove_members([self.email])

    def __unicode__(self):
        return self.email
