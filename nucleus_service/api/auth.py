from rest_framework_httpsignature.authentication import SignatureAuthentication
from django.contrib.auth.models import User
from api.models import Nonce
from rest_framework import exceptions

import time

import traceback


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

        if(abs(ts_diff) > self.TIME_BACK):
            raise exceptions.AuthenticationFailed(
                'Timestamp is more than %s minutes different from the server.' % TIME_BACK)

        try:
            nonce = Nonce(nonce=nonce, timestamp=ts)
            nonce.save(force_insert=True)
        except:
            raise exceptions.AuthenticationFailed('Nonce check failed')

        return SignatureAuthentication.authenticate(self, request)
