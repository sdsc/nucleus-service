from __future__ import absolute_import

from celery import shared_task, Task
from subprocess import Popen, PIPE
import json
import sys, traceback

@shared_task(ignore_result=True)
def submit_computesetjob(self, cset_job_json):
    """ This task runs on comet-fe1 therefore database updates can ONLY occur
        using update_computesetjob() which will run on comet-nucleus
    """
    import logging
    from api.models import ComputeSetJob, CSETJOB_STATE_SUBMITTED, CSETJOB_STATE_FAILED, CSETJOB_STATE_RUNNING, CSETJOB_STATE_COMPLETED
    from api.serializers import ComputeSetJobSerializer

    FORMAT = "%(asctime)-15s %(computeset)s %(error)s %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)
    logger = logging.getLogger(__name__)

    cset_job = json.loads(cset_job_json)

    cset_job["name"] = "VC-JOB-%s-%s" % (cset_job["computeset_id"],
        str(self.request.id).replace('-',''))
    cset_job["jobid"] = None
    cset_job["error"] = None

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
        '--job-name=%s' % (cset_job['name']),
        '--output=%s.out' % (cset_job['name']),
        '--workdir=/tmp',
        '--parsable',
        '--partition=virt',
        '--nodes=%s-%s' % (cset_job['nodes'], cset_job['nodes']),
        '--ntasks-per-node=1',
        '--cpus-per-task=24',
        '--signal=B:USR1@60',
        '--time=%s' % (cset_job['walltime_mins']),
        '/etc/slurm/VC-JOB.run',
        '%s' % (cset_job['walltime_mins'])]

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        cset_job["jobid"] = output.rstrip().strip()
        cset_job["state"] = ComputeSetJob.CSETJOB_STATE_SUBMITTED
        serializer = ComputeSetJobSerializer(cset_job)
        update_computesetjob.delay(serializer.data)

    except OSError as e:
        cset_job["state"] = ComputeSetJob.CSETJOB_STATE_FAILED
        d = {'computeset': cset_job["computeset_id"], 'error': e.returncode}
        logger.error("OSError: %s", e.output.strip(), extra=d)

    except subprocess.CalledProcessError as e:
        cset_job["state"] = ComputeSetJob.CSETJOB_STATE_FAILED
        if e.returncode == 124:
            d = {'computeset': cset_job["computeset_id"], 'error': e.returncode}
            logger.error("CalledProcessError: Timeout during request: %s", e.output.strip().rstrip(), extra=d)
        else:
            d = {'computeset': cset_job["computeset_id"], 'error': e.returncode}
            logger.error("CalledProcessError: %s", e.output.strip().rstrip(), extra=d)


@shared_task(ignore_result=True)
def update_computesetjob(cset_job_json):
    """ This task runs on comet-nucleus and can update the database """
    from api.models import ComputeSet
    from api.models import ComputeSetJob, CSETJOB_STATE_SUBMITTED, CSETJOB_STATE_FAILED, CSETJOB_STATE_RUNNING, CSETJOB_STATE_COMPLETED
    import hostlist

    try:
        cset_job = ComputeSetJob.objects.get(jobid = cset_job_json["jobid"])

        if (
            cset_job.jobid != cset_job_json["id"] or
            cset_job.nodelist != cset_job_json["nodelist"] or
            ):
            cset_job.jobid = cset_job["jobid"]
            cset_job.nodelist = cset_job["nodelist"]
            cset_job.save()

        if (cset_job.state != cset_job_json["state"]):
            old_cset_job_state = cset_job.state
            cset_job.state = cset_job_json["state"]
            cset_job.save()

            cset = cset_job.computesetjob

            # Job passed from QUEUED to RUNNING state...
            if (
                old_cset_job_state == ComputeSetJob.CSETJOB_STATE_QUEUED and
                cset_job.state == ComputeSetJob.CSETJOB_STATE_RUNNING
                ):
                if cset_job.nodelist is not None:
                    nodes = [compute['name'] for compute in cset.computes]
                    hosts = hostlist.expand_hostlist("%s" % cset_job.nodelist)
                    # TODO: vlan & switchport configuration
                    poweron_nodeset.delay(nodes, hosts)

            # Job passed from QUEUED to COMPLETED state directly...
            if (
                old_cset_job_state == ComputeSetJob.CSETJOB_STATE_QUEUED and
                cset_job.state == ComputeSetJob.CSETJOB_STATE_COMPLETED
                ):
                if cset_job.nodelist is not None:
                    hosts = hostlist.expand_hostlist("%s" % cset_job.nodelist)
                    # TODO: anything else todo?

            # Job passed from RUNNING to COMPLETED state...
            if (
                old_cset_job_state == ComputeSetJob.CSETJOB_STATE_RUNNING and
                cset_job.state == ComputeSetJob.CSETJOB_STATE_COMPLETED
                ):
                if cset_job.nodelist is not None:
                    nodes = [compute['name'] for compute in cset.computes]
                    poweroff_nodes.delay(nodes, "shutdown")
                    # TODO: vlan & switchport de-configuration

    except: ComputeSetJob.DoesNotExist:
        cset_job = None
        d = {'computeset': cset_job_json["id"], 'error': ComputeSetJob.DoesNotExist}
        logger.error("update_computesetjob: %s", "ComputeSetJob does not exist", extra=d)

@shared_task(ignore_result=True)
def poweron_nodeset(nodes, hosts):
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
