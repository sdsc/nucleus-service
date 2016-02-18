from django.http import HttpResponse
from django.template import loader

from decorators import basicauth


@basicauth
def getkey(request):
    template = loader.get_template('getkey.html')
    context = {
        'key_name': request.user.api_key.key_name,
        'key': request.user.api_key.secret
    }
    return HttpResponse(template.render(context, request))
