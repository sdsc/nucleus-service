from __future__ import absolute_import

from celery import shared_task, Task
from subprocess import Popen, PIPE
import json

@shared_task(ignore_result=True)
def poweron_nodeset(nodes, hosts):
    args = ["/root/test/boot-these-nodes-on-these-hosts.sh", " ".join(nodes), " ".join(hosts)]
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return "%s\n%s"%(out, err)

@shared_task(ignore_result=True)
def poweroff_nodes(nodes, action):
    args = ["/opt/rocks/bin/rocks", "stop", "host", "vm", " ".join(nodes), "action=%s"%action]
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return "%s\n%s"%(out, err)

@shared_task(ignore_result=True)
def poweron_nodes(nodes):
    args = ["/opt/rocks/bin/rocks", "start", "host", "vm", " ".join(nodes)]
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return "%s\n%s"%(out, err)
 
@shared_task(ignore_result=True)
def update_clusters(clusters_json):
    from api.models import Cluster, Frontend, Compute
    for cluster_rocks in clusters_json:
        try:
            cluster_obj = Cluster.objects.get(frontend__rocks_name=cluster_rocks["frontend"])
            frontend = Frontend.objects.get(rocks_name = cluster_rocks["frontend"])
            if(frontend.state != cluster_rocks["state"]):
                frontend.state = cluster_rocks["state"]
                frontend.save()
        except Cluster.DoesNotExist:
            frontend = Frontend()
            frontend.name = cluster_rocks["frontend"]
            frontend.rocks_name = cluster_rocks["frontend"]
            frontend.state = cluster_rocks["state"]
            frontend.type = cluster_rocks["type"]
            frontend.save()

            cluster_obj = Cluster()
            cluster_obj.name = cluster_rocks["frontend"]
            cluster_obj.frontend = frontend
            cluster_obj.save()

        for compute_rocks in cluster_rocks["computes"]:
            compute_obj, created = Compute.objects.get_or_create(rocks_name = compute_rocks["name"], cluster = cluster_obj)
            if(created):
                compute_obj.name = compute_rocks["name"]
                compute_obj.state = compute_rocks["state"]
                compute_obj.type = compute_rocks["type"]
                compute_obj.save()
            elif(compute_obj.state != compute_rocks["state"]):
                compute_obj.state = compute_rocks["state"]
                compute_obj.save()
                
