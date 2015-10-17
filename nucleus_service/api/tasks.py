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
def poweron_nodes(nodes, hosts):
    args = ["/root/test/boot-these-nodes-on-these-hosts.sh", " ".join(nodes), " ".join(hosts)]
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return "%s\n%s"%(out, err)

@shared_task(base=CallbackTask, ignore_result=True)
def list_clusters(cluster_id):
    args = ["/opt/rocks/bin/rocks", "list", "cluster", cluster_id, "json=true"]
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    cluster_rocks_desc = json.loads(out)
    res_clust = {
        'name':cluster_id,
        'frontend': cluster_id,
        'ip': 'TBD',
        'clients': []
    }
    for record in cluster_rocks_desc:
        if not record['frontend']:
            res_clust['clients'] = [ 
                    {
                        'name': client['client nodes'],
                        'ip': 'TBD',
                        'type': client['type']
                    } for client in record["cluster"]
                ]
    return res_clust

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


