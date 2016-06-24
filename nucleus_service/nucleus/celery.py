from __future__ import absolute_import

import os

from celery import Celery
from celery.security import setup_security

from nucleus import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nucleus.settings')
os.environ.setdefault('C_FORCE_ROOT', '1')

app = Celery('nucleus', broker='pyamqp://comet-sfe2/nucleus')

app.config_from_object(settings)
app.autodiscover_tasks(['api'], force=True)

app.conf.update(CELERY_ACCEPT_CONTENT=['application/json', 'json'])
app.conf.update(CELERY_TASK_SERIALIZER='auth')
app.conf.update(CELERY_RESULT_SERIALIZER='json')

# This check is for roll installation: if certs are not there, settings won't work
if(os.path.isdir('/var/secrets/cometvc')):
    setup_security(allowed_serializers=['application/json', 'json'])
