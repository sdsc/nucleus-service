from __future__ import absolute_import

from celery import shared_task
from subprocess import Popen, PIPE

@shared_task()
def list_clusters(cluster_id=None):
    res = subprocess.Popen(["/opt/rocks/bin/rocks", "list", "cluster", "json=true"], stdout=PIPE)
    out, err = res.communicate()
    return out


@shared_task()
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)
