#!/usr/bin/python

import json
from subprocess import Popen, PIPE
import traceback

from nucleus.celery import *

from api.tasks import update_clusters

NAS = "comet-image-32-5"

images_req = Popen(['/opt/rocks/bin/rocks', 'list', 'host', 'storagemap', NAS,
                      'json=true'], stdout=PIPE, stderr=PIPE)
(out, err) = images_req.communicate()

images = json.loads(out)[0]["storagemap"]

img_states = {}

for image in images:
    compute = image["zvol"]
    if compute.endswith("-vol"):
        compute = compute[:-4]
    img_states[compute] = {
        'state': image['state'],
        'locked': image['locked'] if image['locked'] else False
    }
    
clusters_req = Popen(['/opt/rocks/bin/rocks', 'list', 'cluster',
                      'json=true', 'status=true'], stdout=PIPE, stderr=PIPE)
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
            'disksize': 0,
            'physhost': None,
            'img_locked': img_states[record['frontend']]['locked'] if img_states.get(record['frontend']) else None,
            'img_state': img_states[record['frontend']]['state'] if img_states.get(record['frontend']) else None,
            'state': record['cluster'][0]['status'],
            'type': record['cluster'][0]['type'],
            'computes': []
        }
        result.append(res_clust)
    else:
        res_clust['computes'] = [
            {
                'name': client['client nodes'],
                'physhost': None,
                'interfaces': [],
                'mem': 0,
                'cpus': 0,
                'disksize': 0,
                'img_locked': img_states[client['client nodes']]['locked'] if img_states.get(client['client nodes']) else None,
                'img_state': img_states[client['client nodes']]['state'] if img_states.get(client['client nodes']) else None,
                'type': client['type'],
                'state': client['status']
            } for client in record["cluster"]
        ]

gateway_req_params = ['/opt/rocks/bin/rocks', 'list', 'host', 'route']
gateway_req_params.extend(cluster['frontend'] for cluster in result)
gateway_req_params.append('json=true')
gateway_req = Popen(gateway_req_params, stdout=PIPE, stderr=PIPE)
(out, err) = gateway_req.communicate()
routes = json.loads(out)

for cluster in result:
    try:
        cluster_routes = (route for route in routes if route['host'] == cluster['frontend']).next()['route']
        cluster['gateway'] = (route for route in cluster_routes if route['network'] == "0.0.0.0").next()['gateway']
    except:
        traceback.print_exc()

    try:
        fe_req = Popen(['/opt/rocks/bin/rocks', 'list', 'host', 'interface',
                        cluster['frontend'], 'json=true'], stdout=PIPE, stderr=PIPE)
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

        vm_req = Popen(['/opt/rocks/bin/rocks', 'list', 'host', 'vm',
                        cluster['frontend'], 'json=true', 'showdisks=true'], stdout=PIPE, stderr=PIPE)
        (out, err) = vm_req.communicate()
        if out:
            for vm_rec in json.loads(out)[0]["vm"]:
                if(not cluster.get("physhost")):
	            cluster["physhost"] = vm_rec["host"]
                if(vm_rec["mem"]):
                    cluster["mem"] = vm_rec["mem"]
                    cluster["cpus"] = vm_rec["cpus"]
                    cluster["disksize"] = vm_rec["disksize"]

        if(not cluster['computes']):
            continue

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
                    next(compute for compute in cluster['computes'] if compute[
                         'name'] == rec['host'])['interfaces'].append(interface)

        args = ['/opt/rocks/bin/rocks', 'list', 'host', 'vm']
        args.extend([compute['name'] for compute in cluster['computes']])
        args.extend(['json=true', 'showdisks=true'])
        vm_req = Popen(args, stdout=PIPE, stderr=PIPE)
        (out, err) = vm_req.communicate()
        if out:
            for vm_rec in json.loads(out):
                compute = next(compute for compute in cluster['computes'] if compute[
                     'name'] == vm_rec['vm-host'])
                if(not compute.get("physhost")):
	            compute["physhost"] = vm_rec["vm"][0]["host"]
                compute["mem"] = vm_rec["vm"][0]["mem"]
                compute["cpus"] = vm_rec["vm"][0]["cpus"]
                compute["disksize"] = vm_rec["vm"][0]["disksize"]

    except:
        # print "Unexpected error:", traceback.print_tb(sys.exc_info()[2])
        traceback.print_exc()


update_clusters.delay(result)
#print(json.dumps(result))
