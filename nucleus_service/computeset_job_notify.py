#!/usr/bin/env python

import json
import os
from api.tasks import update_computesetjob

request = {'stage': None, 'state': None, 'jobid': None, 'name': None}

if os.environ.has_key('COMPUTESET_JOB_STAGE'):
    request['stage'] = str(os.environ['COMPUTESET_JOB_STAGE'])

if os.environ.has_key('COMPUTESET_JOB_STATE'):
    request['state'] = str(os.environ['COMPUTESET_JOB_STATE'])

if os.environ.has_key('SLURM_JOB_ID'):
    request['jobid'] = str(os.environ['SLURM_JOB_ID'])

if os.environ.has_key('SLURM_JOB_NAME'):
    request['name'] = str(os.environ['SLURM_JOB_NAME'])

if os.environ.has_key('SLURM_JOB_NODELIST'):
    request['nodelist'] = str(os.environ['SLURM_JOB_NODELIST'])

update_computesetjob.delay(request)
