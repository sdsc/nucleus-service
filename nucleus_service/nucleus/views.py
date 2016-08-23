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

