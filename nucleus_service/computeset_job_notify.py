#!/usr/bin/env python

import os
from api.tasks import update_computeset
import time

from nucleus.celery import *

request = {'stage': None, 'state': None, 'jobid': None, 'name': None, 'computeset': None}

if os.environ.has_key('COMPUTESET_JOB_STAGE'):
    request['stage'] = str(os.environ['COMPUTESET_JOB_STAGE'])

if os.environ.has_key('COMPUTESET_JOB_STATE'):
    request['state'] = str(os.environ['COMPUTESET_JOB_STATE'])

if os.environ.has_key('SLURM_JOB_ID'):
    request['jobid'] = str(os.environ['SLURM_JOB_ID'])

if os.environ.has_key('SLURM_JOB_NAME'):
    request['name'] = str(os.environ['SLURM_JOB_NAME'])
    request['id'] = int(request['name'].split('-')[2])

if os.environ.has_key('SLURM_JOB_NODELIST'):
    request['nodelist'] = str(os.environ['SLURM_JOB_NODELIST'])

request['start_time'] = int(time.time())

update_computeset.delay(request)
