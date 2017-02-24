from __future__ import absolute_import

import os

from celery import Celery
from celery.security import setup_security

from nucleus import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nucleus.settings')
os.environ.setdefault('C_FORCE_ROOT', '1')

rabbitmq_server = "localhost"
if(os.path.isfile('/opt/rocks/etc/rabbitmq.conf')):
    with open('/opt/rocks/etc/rabbitmq.conf', 'r') as \
        rabbit_url_file:
        rabbitmq_server = rabbit_url_file.read().rstrip('\n')


app = Celery('nucleus', broker='pyamqp://%s/nucleus'%rabbitmq_server)

app.config_from_object(settings)
app.autodiscover_tasks(['api'], force=True)

app.conf.update(CELERY_ACCEPT_CONTENT=['application/json', 'json'])
app.conf.update(CELERY_TASK_SERIALIZER='auth')
app.conf.update(CELERY_RESULT_SERIALIZER='json')

# This check is for roll installation: if certs are not there, settings won't work
if(os.path.isfile('/var/secrets/cometvc/key.pem') and
	os.path.isfile('/var/secrets/cometvc/cert.pem') and
	os.path.isfile('/var/secrets/cometvc/ca.pem')
	):
    setup_security(allowed_serializers=['application/json', 'json'])
