class EmailUtils():
    @staticmethod
    def add_existent_email(email_set, email_obj):
        """
        Adds an existent email to email_set. Takes care to change the username and
        primary email of the email's old account if necessary.
        """
        EmailUtils.change_owner_info(email_obj)

        # now we can safely add this email to email_set
        email_set.add(email_obj)

    @staticmethod
    def change_owner_info(email_obj):
        """
        If necessary, changes the owner of email_obj to not have
        a username or primary email NOT equal to email_obj's email.
        """
        owner = email_obj.user
        email = email_obj.email

        if owner.username == email or owner.email == email:
            # need to change old_user's username and primary email
            diff_email = EmailUtils._get_different_email(owner, email_obj)
            if diff_email:
                owner.email = diff_email
                owner.username = diff_email
                owner.save()
            else:
                # there are no other emails for this account, so deactivate it
                owner.deactivate()

    @staticmethod
    def _get_different_email(user, email_obj):
        """
        Returns an email for the user that isn't the email held by email_obj,
        or returns None if email is the only email for user.

        This code might do unnecessary database lookups.
        """
        for user_email in user.email_set.all():
            if user_email.email != email_obj.email:
                return user_email.email
        return None
