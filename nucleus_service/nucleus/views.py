from django.http import HttpResponse
from django.template import loader

from decorators import basicauth
import json
from api.models import NucleusUser
from django.utils.crypto import get_random_string
from rest_framework import status

import pam as pam_base
from django.contrib.auth import get_user_model

@basicauth
def getkey(request):
    mime_req = request.META.get('HTTP_ACCEPT', 'text/html')
   
    if(not hasattr(request.user, 'api_key')):
        request.user.api_key = NucleusUser.objects.create(key_name=request.user.email, user_id=request.user.id, secret=get_random_string(24))
        request.user.save()

    if("text/html" in mime_req or mime_req == "*/*"):
        template = loader.get_template('getkey.html')
        context = {
            'key_name': request.user.api_key.key_name,
            'key': request.user.api_key.secret
        }
        return HttpResponse(template.render(context, request))
    elif ("application/json" in mime_req):
        return_struct = {
            "key_name": request.user.api_key.key_name,
            'key': request.user.api_key.secret
        }
        return HttpResponse(json.dumps(return_struct), content_type=mime_req)
    else:
        return HttpResponse("Unsupported Accept header %s"%mime_req, status=415)

def getyubikey(request):
        UserModel = get_user_model()

        if (not request.META.get("HTTP_USERNAME")) or (not request.META.get("HTTP_PASSWORD")):
            return HttpResponse("Not found username and password headers",
                            status=status.HTTP_400_BAD_REQUEST)

        _pam = pam_base.pam()
        username = request.META['HTTP_USERNAME']
        password = request.META['HTTP_PASSWORD']
        user = None

        if _pam.authenticate(username, password, "nucleus"):
            try:
                user = UserModel._default_manager.get_by_natural_key(
                    username=username)

                mime_req = request.META.get('HTTP_ACCEPT', 'text/html')

                if(not hasattr(user, 'api_key')):
                    user.api_key = NucleusUser.objects.create(key_name=user.email, user_id=user.id, secret=get_random_string(24))
                    user.save()

                if("text/html" in mime_req or mime_req == "*/*"):
                    template = loader.get_template('getkey.html')
                    context = {
                        'key_name': user.api_key.key_name,
                        'key': user.api_key.secret
                    }
                    return HttpResponse(template.render(context, request))
                elif ("application/json" in mime_req):
                    return_struct = {
                        "key_name": user.api_key.key_name,
                        'key': user.api_key.secret
                    }
                    return HttpResponse(json.dumps(return_struct), content_type=mime_req)
                else:
                    return HttpResponse("Unsupported Accept header %s"%mime_req, status=415)

            except UserModel.DoesNotExist, e:
                return HttpResponse("User not found", status=status.HTTP_404_NOT_FOUND)

        return HttpResponse("Forbidden",
                        status=status.HTTP_403_FORBIDDEN)
