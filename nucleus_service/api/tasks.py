from __future__ import absolute_import

from celery import shared_task, Task
from subprocess import Popen, PIPE
import json


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        store_result.delay(task_id, retval)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@shared_task(base=CallbackTask, ignore_result=True)
def list_clusters(cluster_id=None):
    args = ["/opt/rocks/bin/rocks", "list", "cluster", "json=true"]
    if(cluster_id):
        args.append(cluster_id)
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return json.loads(out)

@shared_task(ignore_result=True)
def store_result(task_id, result):
    from api.models import Call
    cur_call = Call.objects.get(pk = task_id)
    try:
        cur_call.data = json.dumps(result)
    except TypeError:
        cur_call.data = str(result)
    cur_call.status = 1
    cur_call.save()


