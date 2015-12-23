from __future__ import absolute_import

from celery import shared_task, Task
from subprocess import Popen, PIPE, check_output, STDOUT, CalledProcessError
import json
import sys, traceback

ISOS_DIR = "/mnt/images"

@shared_task(ignore_result=True)
def submit_computeset(cset):
    """ This task runs on comet-fe1 therefore database updates can ONLY occur
        using update_computeset() which will run on comet-nucleus.
        In addition, since django.db modules are not installed on comet-fe1
        we need to use json module to deserialize/serialize JSON.
    """
    from api.tasks import update_computeset
    import uuid

    cset["name"] = "VC-JOB-%s-%s" % (cset["id"],
        str(uuid.uuid1()).replace('-',''))
    cset["jobid"] = None
    cset["error"] = None

    # There are a number of potentilly configurable parameters in the following call
    # to sbatch..
    #
    # workdir=/tmp will leave the job .out file on the EXEC_HOST in /tmp
    # partition=virt will submit jobs to the virt partition
    # signal=B:USR1@60 will send a USR1 signal to the batch script running on the
    # EXEC_HOST. The signal will be caught by the signal_handler and the jobscript
    # should request shutdown of the virtual compute nodes.
    #
    # All other parameters should be considered UNCHANGABLE.

    cmd = ['/usr/bin/timeout',
        '2',
        '/usr/bin/sbatch',
        '--job-name=%s' % (cset['name']),
        '--output=%s.out' % (cset['name']),
	    '--uid=%s' % (cset['user']),
	    '--account=%s' % (cset['account']),
        '--workdir=/tmp',
        '--parsable',
        '--partition=virt',
        '--nodes=%s-%s' % (cset['node_count'], cset['node_count']),
        '--ntasks-per-node=1',
        '--cpus-per-task=24',
        '--signal=B:USR1@60',
        '--time=%s' % (cset['walltime_mins']),
        '/etc/slurm/VC-JOB.run',
        '%s' % (cset['walltime_mins'])]

    try:
        output = check_output(cmd, stderr=STDOUT)
        cset["jobid"] = output.rstrip().strip()
        cset["state"] = "submitted"
        update_computeset.delay(cset)

    except OSError as e:
        cset["state"] = "failed"
        msg = "OSError: %s" % (e)
        update_computeset.delay(cset)
        print msg

    except CalledProcessError as e:
        cset["state"] = "failed"
        if e.returncode == 124:
            msg = "CalledProcessError: Timeout during request: %s" % (e.output.strip().rstrip())
        else:
            msg = "CalledProcessError: %s" % (e.output.strip().rstrip())
        update_computeset.delay(cset)
        print msg

@shared_task(ignore_result=True)
def update_computeset(cset_json):
    """ This task runs on comet-nucleus and can update the database """
    from api.models import ComputeSet
    from api import hostlist

    try:
        cset = ComputeSet.objects.get(id=cset_json['id'])

        cset.jobid = cset_json["jobid"]

        if ("name" in cset_json):
            cset.name = cset_json["name"]

        if ("user" in cset_json):
            cset.user = cset_json["user"]

        if("account" in cset_json):
            cset.account = cset_json["account"]

        if ("walltime_mins" in cset_json):
            cset.walltime_mins = cset_json["walltime_mins"]

        if ("node_count" in cset_json):
            cset.node_count = cset_json["node_count"]

        cset.save()

	    #The following will only exist after jobscript barrier...
        if ("nodelist" in cset_json):
            cset.nodelist = cset_json["nodelist"]
            cset.save()

        old_cset_state = None
        if ("state" in cset_json):
            old_cset_state = cset.state
            if (cset.state != cset_json["state"]):
                cset.state = cset_json["state"]
                cset.save()

            # Job passed from SUBMITTED to RUNNING state...
            if (
                old_cset_state == ComputeSet.CSET_STATE_SUBMITTED and
                cset.state == ComputeSet.CSET_STATE_RUNNING
                ):
                if cset.nodelist is not None:
                    cset = ComputeSet.objects.get(pk=cset.id)
                    nodes = []
                    for compute in cset.computes.all():
                        nodes.append(compute.rocks_name)

                    hosts = hostlist.expand_hostlist("%s" % cset.nodelist)
                    # TODO: vlan & switchport configuration
                    poweron_nodeset.delay(nodes, hosts, None)

            # Job passed from SUBMITTED to COMPLETED state directly...
            if (
                old_cset_state == ComputeSet.CSET_STATE_SUBMITTED and
                cset.state == ComputeSet.CSET_STATE_COMPLETED
                ):
                if cset.nodelist is not None:
                    hosts = hostlist.expand_hostlist("%s" % cset.nodelist)
                    # TODO: anything else todo?

            # Job passed from RUNNING to COMPLETED state...
            if (
                old_cset_state == ComputeSet.CSET_STATE_RUNNING and
                cset.state == ComputeSet.CSET_STATE_COMPLETED
                ):
                if cset.nodelist is not None:
                    nodes = [compute['name'] for compute in cset.computes]
                    poweroff_nodes.delay(nodes, "shutdown")
                    # TODO: vlan & switchport de-configuration

    except ComputeSet.DoesNotExist:
        cset = None
        msg = "update_computeset: %s" % ("ComputeSet (%d) does not exist" % (cset_json["id"]))

@shared_task(ignore_result=True)
def poweron_nodeset(nodes, hosts, iso_name):
    if(hosts and (len(nodes) != len(hosts))):
        print "hosts length is not equal to nodes"
        return
    outb = ""
    errb = ""
    if(hosts):
        for node, host in zip(nodes, hosts):
            res = Popen(["/opt/rocks/bin/rocks", "set", "host", "vm", "%s"%node, "physnode=%s"%host], stdout=PIPE, stderr=PIPE)
            out, err = res.communicate()
            outb += out
            errb += err
    if(iso_name):
        (ret_code, out, err) = _attach_iso(nodes, iso_name)
        if(ret_code):
            outb += out
            errb += err
            return "Error adding iso to nodes: %s\n%s"%(outb, errb)
    args = ["/opt/rocks/bin/rocks", "start", "host", "vm"]
    args.extend(nodes)
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    outb += out
    errb += err
    return "%s\n%s"%(outb, errb)

@shared_task(ignore_result=True)
def poweroff_nodes(nodes, action):
    args = ["/opt/rocks/bin/rocks", "stop", "host", "vm"]
    args.extend(nodes)
    args.append("action=%s"%action)
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return "%s\n%s"%(out, err)

@shared_task(ignore_result=True)
def attach_iso(nodes, iso_name):
    (ret_code, out, err) = _attach_iso(nodes, iso_name)
    if(ret_code):
        return "%s\n%s"%(out, err)


# Local function to be called from multiple tasks
def _attach_iso(nodes, iso_name):
    args = ["/opt/rocks/bin/rocks", "set", "host", "vm", "cdrom"]
    args.extend(nodes)
    if(iso_name):
        args.append("cdrom=%s/%s"%(ISOS_DIR, iso_name))
    else:
        args.append("cdrom=none")
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return (res.returncode, out, err)

@shared_task(ignore_result=True)
def poweron_nodes(nodes):
    args = ["/opt/rocks/bin/rocks", "start", "host", "vm"]
    args.extend(nodes)
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return "%s\n%s"%(out, err)

@shared_task(ignore_result=True)
def update_clusters(clusters_json):
    from api.models import Cluster, Frontend, Compute, ComputeSet, FrontendInterface, ComputeInterface, COMPUTESET_STATE_STARTED, COMPUTESET_STATE_COMPLETED, COMPUTESET_STATE_QUEUED
    for cluster_rocks in clusters_json:
        try:
            cluster_obj = Cluster.objects.get(frontend__rocks_name=cluster_rocks["frontend"])

            if(cluster_obj.vlan != cluster_rocks["vlan"]):
                cluster_obj.vlan = cluster_rocks["vlan"]
                cluster_obj.save()

            frontend = Frontend.objects.get(rocks_name = cluster_rocks["frontend"])
            if(frontend.state != cluster_rocks["state"] or frontend.memory != cluster_rocks["mem"] or frontend.cpus != cluster_rocks["cpus"]):
                frontend.state = cluster_rocks["state"]
                frontend.memory = cluster_rocks["mem"]
                frontend.cpus = cluster_rocks["cpus"]
                frontend.save()
        except Cluster.DoesNotExist:
            frontend = Frontend()
            frontend.name = cluster_rocks["frontend"]
            frontend.rocks_name = cluster_rocks["frontend"]
            frontend.state = cluster_rocks["state"]
            frontend.memory = cluster_rocks["mem"]
            frontend.cpus = cluster_rocks["cpus"]
            frontend.type = cluster_rocks["type"]
            frontend.save()

            cluster_obj = Cluster()
            cluster_obj.name = cluster_rocks["frontend"]
            cluster_obj.vlan = cluster_rocks["vlan"]
            cluster_obj.frontend = frontend
            cluster_obj.save()

        cluster_obj = Cluster.objects.get(frontend__rocks_name=cluster_rocks["frontend"])
        frontend = Frontend.objects.get(rocks_name = cluster_rocks["frontend"])
        for interface in cluster_rocks['interfaces']:
            if(interface["mac"]):
                if_obj, created = FrontendInterface.objects.update_or_create(frontend = frontend, ip = interface["ip"], netmask = interface["netmask"], mac = interface["mac"], iface=interface["iface"], subnet=interface["subnet"])

        for compute_rocks in cluster_rocks["computes"]:
            compute_obj, created = Compute.objects.get_or_create(rocks_name = compute_rocks["name"], cluster = cluster_obj)
            if(created):
                compute_obj.name = compute_rocks["name"]
                compute_obj.state = compute_rocks["state"]
                compute_obj.memory = compute_rocks["mem"]
                compute_obj.cpus = compute_rocks["cpus"]
                compute_obj.type = compute_rocks["type"]
                compute_obj.save()
            elif(compute_obj.state != compute_rocks["state"] or compute_obj.memory != compute_rocks["mem"] or compute_obj.cpus != compute_rocks["cpus"]):
                compute_obj.state = compute_rocks["state"]
                compute_obj.memory = compute_rocks["mem"]
                compute_obj.cpus = compute_rocks["cpus"]
                compute_obj.save()
                try:
                    cs = ComputeSet.objects.get(computes__id__exact=compute_obj.id, state__in=[COMPUTESET_STATE_QUEUED, COMPUTESET_STATE_STARTED])
                    if cs.state == COMPUTESET_STATE_QUEUED and compute_obj.state == "active":
                        cs.state = COMPUTESET_STATE_STARTED
                        cs.save()
                    elif cs.state == COMPUTESET_STATE_STARTED and (not cs.computes.filter(state="active")):
                        cs.state = COMPUTESET_STATE_COMPLETED
                        cs.save()
                except ComputeSet.DoesNotExist:
                    print "Computeset for compute %s not found"%compute_obj.name
                except:
                    print traceback.format_exc()

            for interface in compute_rocks['interfaces']:
                if(interface["mac"]):
                    if_obj, created = ComputeInterface.objects.update_or_create(compute = compute_obj, ip = interface["ip"], netmask = interface["netmask"], mac = interface["mac"], iface=interface["iface"], subnet=interface["subnet"])
