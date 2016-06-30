import time

from django.contrib.auth.models import User
from rest_framework_httpsignature.authentication import SignatureAuthentication
from rest_framework import exceptions

from api.models import Nonce

from django_pam.auth.backends import PAMBackend
import pam as pam_base
from django.contrib.auth import get_user_model
import sys

class NucleusAPISignatureAuthentication(SignatureAuthentication):
    # The HTTP header used to pass the consumer key ID.
    # Defaults to 'X-Api-Key'.
    API_KEY_HEADER = 'X-Api-Key'
    TIME_BACK = 30 * 60

    # A method to fetch (User instance, user_secret_string) from the
    # consumer key ID, or None in case it is not found.
    def fetch_user_data(self, api_key):
        try:
            user = User.objects.get(api_key=api_key)
            return (user, user.api_key.secret)
        except User.DoesNotExist:
            return None

    def authenticate(self, request):

        api_key_header = self.header_canonical(self.API_KEY_HEADER)
        api_key = request.META.get(api_key_header)
        if not api_key:
            return None

        nonce = request.META.get(self.header_canonical("nonce"))
        if not nonce:
            raise exceptions.AuthenticationFailed('No nonce provided')

        ts = request.META.get(self.header_canonical("timestamp"))
        if not ts:
            raise exceptions.AuthenticationFailed('No timestamp provided')

        ts_diff = int(time.time()) - int(ts)

        if abs(ts_diff) > self.TIME_BACK:
            raise exceptions.AuthenticationFailed(
                'Timestamp is more than %s minutes different from the server.' % TIME_BACK)

        try:
            nonce = Nonce(nonce=nonce, timestamp=ts)
            nonce.save(force_insert=True)
        except:
            raise exceptions.AuthenticationFailed('Nonce check failed')

        return SignatureAuthentication.authenticate(self, request)



class NucleusPAMBackend(PAMBackend):
    """
    An implementation of a PAM backend authentication module.
    """
    _pam = pam_base.pam()

    def authenticate(self, username=None, password=None, service=None, **extra_fields):
        """
        Authenticate using PAM then get the account if it exists else create
        a new account.
        :param username: The users username. This is a manditory field.
        :type username: str
        :param password: The users password. This is a manditory field.
        :type password: str
        :param extra_fields: Additonal keyword options of any editable field
                             in the user model.
        :type extra_fields: dict
        :rtype: The Django user object.
        """
        UserModel = get_user_model()
        user = None

        if self._pam.authenticate(username, password, "nucleus"):
            try:
                user = UserModel._default_manager.get_by_natural_key(
                    username=username)
            except UserModel.DoesNotExist:
                print "User %s not found in the database"%username
            except:
                print "Unexpected error:", sys.exc_info()[1]

        return user
