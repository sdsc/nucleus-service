#!/usr/bin/python

from subprocess import Popen, PIPE
import json
import sys, traceback
from api.tasks import update_clusters

from nucleus.celery import *

clusters_req = Popen(['/opt/rocks/bin/rocks','list','cluster','json=true', 'status=true'], stdout=PIPE, stderr=PIPE)
(out, err) = clusters_req.communicate()

clusters = json.loads(out)

result = []

for record in clusters:
	if record['frontend']:
	    res_clust = {
		'frontend': record['frontend'],
		'interfaces': [],
		'mem': 0,
		'cpus': 0,
		'state': record['cluster'][0]['status'],
		'type': record['cluster'][0]['type'],
		'computes': []
	    }
	else:
	    res_clust['computes'] = [
		    {
			'name': client['client nodes'],
			'interfaces': [],
			'mem': 0,
			'cpus': 0,
			'type': client['type'],
			'state': client['status']
		    } for client in record["cluster"]
		]
	    result.append(res_clust)

for cluster in result:
    try:
        fe_req = Popen(['/opt/rocks/bin/rocks', 'list', 'host', 'interface', cluster['frontend'], 'json=true'], stdout=PIPE, stderr=PIPE)
        (out, err) = fe_req.communicate()
        if out:
            for if_rec in json.loads(out)[0]['interface']:
                interface = {
                    'ip': if_rec['ip'],
                    'mac': if_rec['mac'],
                    'iface': if_rec['iface'],
                    'netmask': if_rec['netmask'],
                    'subnet': if_rec['subnet']
                }
                cluster['interfaces'].append(interface)
                if(if_rec['subnet'] == 'private'):
                    cluster['vlan'] = if_rec['vlan']

        vm_req = Popen(['/opt/rocks/bin/rocks', 'list', 'host', 'vm', cluster['frontend'], 'json=true'], stdout=PIPE, stderr=PIPE)
        (out, err) = vm_req.communicate()
        if out:
            for vm_rec in json.loads(out)[0]["vm"]:
                if(vm_rec["mem"]):
                    cluster["mem"] = vm_rec["mem"]
                    cluster["cpus"] = vm_rec["cpus"]


        args = ['/opt/rocks/bin/rocks', 'list', 'host', 'interface']
        args.extend([compute['name'] for compute in cluster['computes']])
        args.append('json=true')
        fe_req = Popen(args, stdout=PIPE, stderr=PIPE)
        (out, err) = fe_req.communicate()
        if out:
            for rec in json.loads(out):
                for if_rec in rec['interface']:
                    interface = {
                        'ip': if_rec['ip'],
                        'mac': if_rec['mac'],
                        'iface': if_rec['iface'],
                        'netmask': if_rec['netmask'],
                        'subnet': if_rec['subnet'],
                    }
                    next(compute for compute in cluster['computes'] if compute['name'] == rec['host'])['interfaces'].append(interface)

        vm_req = Popen(['/opt/rocks/bin/rocks', 'list', 'host', 'vm', cluster['frontend'], 'json=true'], stdout=PIPE, stderr=PIPE)
        (out, err) = vm_req.communicate()
        if out:
            for vm_rec in json.loads(out)[0]["vm"]:
                if(vm_rec["mem"]):
                    compute["mem"] = vm_rec["mem"]
                    compute["cpus"] = vm_rec["cpus"]

    except:
        #print "Unexpected error:", traceback.print_tb(sys.exc_info()[2])
	traceback.print_exc()

update_clusters.delay(result)
#print(json.dumps(result))
