from __future__ import absolute_import

import os

from celery import Celery
from celery.security import setup_security

import ssl
from nucleus import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nucleus.settings')
os.environ.setdefault('C_FORCE_ROOT', '1')

rabbitmq_server = "localhost"
if(os.path.isfile('/opt/rocks/etc/rabbitmq.conf')):
    with open('/opt/rocks/etc/rabbitmq.conf', 'r') as \
        rabbit_url_file:
        rabbitmq_server = rabbit_url_file.read().rstrip('\n')


app = Celery('nucleus', broker='pyamqp://%s/nucleus'%rabbitmq_server)


app.conf.update(
    task_routes=(
    {'api.tasks.submit_computeset':
     {'queue': 'frontend'}
     },
    {'api.tasks.cancel_computeset':
     {'queue': 'frontend'}
     },
    {'api.tasks.poweron_nodeset':
     {'queue': 'frontend'}
     },
    {'api.tasks.poweron_nodes':
     {'queue': 'frontend'}
     },
    {'api.tasks.poweroff_nodes':
     {'queue': 'frontend'}
     },
    {'api.tasks.attach_iso':
     {'queue': 'frontend'}
     },
    {'api.tasks.update_computeset':
     {'queue': 'update'}
     },
    {'api.tasks.update_clusters':
     {'queue': 'update'}
     }
    ),
    broker_login_method='EXTERNAL',
    broker_use_ssl={
      'keyfile': '/var/secrets/cometvc/key.pem',
      'certfile': '/var/secrets/cometvc/cert.pem',
      'ca_certs': '/var/secrets/cometvc/ca.pem',
      'cert_reqs': ssl.CERT_REQUIRED
    },
    task_serializer='auth',
    security_key='/var/secrets/cometvc/key.pem',
    security_certificate='/var/secrets/cometvc/cert.pem',
    security_cert_store='/var/secrets/cometvc/pub/*.pem'
)

app.autodiscover_tasks(['api'])

# This check is for roll installation: if certs are not there, settings won't work
if(os.path.isfile('/var/secrets/cometvc/key.pem') and
	os.path.isfile('/var/secrets/cometvc/cert.pem') and
	os.path.isfile('/var/secrets/cometvc/ca.pem')
	):
    setup_security(allowed_serializers=['application/json', 'json'])
