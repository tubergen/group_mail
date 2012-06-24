from django.contrib.auth.tokens import PasswordResetTokenGenerator
from group_mail.apps.common.models import Email


class ClaimEmailTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for 'claim email' requests. We take the email as an
    argument to our public functions and use the user who currently owns
    the account to generate the token.

    Since this user will change if the request goes through, we should be
    guaranteed that the token works only once.

    Further, this user is guaranteed to exist (else we wouldn't be doing
    a claim email), so this should work regardless of whether the claiming
    user exists yet.
    """
    def make_token(self, email):
        user = Email.objects.get(email=email).user
        return super(ClaimEmailTokenGenerator, self).make_token(user)

    def check_token(self, email, token):
        user = Email.objects.get(email=email).user
        return super(ClaimEmailTokenGenerator, self).check_token(user, token)

claim_email_token_generator = ClaimEmailTokenGenerator()
