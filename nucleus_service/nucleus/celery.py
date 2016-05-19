from __future__ import absolute_import

import os

from celery import Celery
from celery.security import setup_security

from nucleus import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nucleus.settings')
os.environ.setdefault('C_FORCE_ROOT', '1')

app = Celery('nucleus', broker='amqp://celery:nimda_celery@comet-fe1/celery')

setup_security();
app.config_from_object(settings)
app.autodiscover_tasks(['api'], force=True)

app.conf.update(CELERY_ACCEPT_CONTENT=['json'])
app.conf.update(CELERY_TASK_SERIALIZER='json')
app.conf.update(CELERY_RESULT_SERIALIZER='json')
