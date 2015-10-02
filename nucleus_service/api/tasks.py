from __future__ import absolute_import

from celery import shared_task
from subprocess import Popen, PIPE
import json

@shared_task()
def list_clusters(cluster_id=None):
    args = ["/opt/rocks/bin/rocks", "list", "cluster", "json=true"]
    if(cluster_id):
        args.append(cluster_id)
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return json.loads(out)
