#!/usr/bin/env python

import json
from os import environ
from api.tasks import update_computesetjob

request = {'stage': None, 'id': None, 'host': None, 'state': None}
request['stage'] = str(environ['COMPUTESET_JOB_STAGE'])
request['jobid'] = str(environ['SLURM_JOB_ID'])
request['host'] = str(environ['SLURMD_NODENAME'])
request['state'] = str(environ['COMPUTESET_JOB_STATE'])
request['nodelist'] = str(environ['SLURM_JOB_NODELIST'])

update_computesetjob.delay(request)
