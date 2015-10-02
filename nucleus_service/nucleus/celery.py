from __future__ import absolute_import

import os

from celery import Celery

from nucleus import settings

app = Celery('nucleus', broker='amqp://celery:nimda_celery@comet-fe1/celery')

app.config_from_object(settings)
app.autodiscover_tasks(['api'], force=True)

app.conf.update(
    CELERY_RESULT_BACKEND='rpc://',
)
app.conf.update(CELERY_ACCEPT_CONTENT = ['json'])
app.conf.update(CELERY_TASK_SERIALIZER = 'json')
app.conf.update(CELERY_RESULT_SERIALIZER = 'json')

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
