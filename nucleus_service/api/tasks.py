from __future__ import absolute_import

from subprocess import Popen, PIPE, check_output, STDOUT, CalledProcessError
import traceback
import syslog

from celery import shared_task
syslog.openlog('nucleus-service', syslog.LOG_PID, syslog.LOG_USER)

ISOS_DIR = "/mnt/images"


@shared_task(ignore_result=True)
def submit_computeset(cset):
    """ This task runs on comet-fe1 therefore database updates can ONLY occur
        using update_computeset() which will run on comet-nucleus.
        In addition, since django.db modules are not installed on comet-fe1
        we need to use json module to deserialize/serialize JSON.
    """
    import uuid

    syslog.syslog(syslog.LOG_DEBUG, "submit_computeset() running")
    cset["name"] = "VC-JOB-%s-%s" % (cset["id"],
                                     str(uuid.uuid1()).replace('-', ''))
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
           '--workdir=/home/%s/VC-JOBS' % (cset['user']),
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
        syslog.syslog(syslog.LOG_INFO, "Submitting computeset job %s" % cset['name'])

    except OSError as e:
        cset["state"] = "failed"
        msg = "OSError: %s" % (e)
        update_computeset.delay(cset)
        syslog.syslog(syslog.LOG_ERR, msg)

    except CalledProcessError as e:
        cset["state"] = "failed"
        if e.returncode == 124:
            msg = "CalledProcessError: Timeout during request: %s" % (
                e.output.strip().rstrip())
        else:
            msg = "CalledProcessError: %s" % (e.output.strip().rstrip())
        update_computeset.delay(cset)
        syslog.syslog(syslog.LOG_ERR, msg)

@shared_task(ignore_result=True)
def cancel_computeset(cset):
    """ Sending --signal=USR1 to a running computeset job will allow it exit
        in the same manner as when the computeset job reaches it walltime_mins
        limit and is signalled by Slurm to exit.
        Actual poweroff of the nodes is handled by the jobscript and/or epilog.
    """
    from api.tasks import update_computeset
    syslog.syslog(syslog.LOG_DEBUG, "cancel_computeset() running")

    cmd = ['/usr/bin/timeout',
           '2',
           '/usr/bin/scancel',
           '--batch',
           '--quiet',
           '--signal=USR1',
           '%s' % (cset['jobid'])]

    try:
        output = check_output(cmd, stderr=STDOUT)
        cset["state"] = "cancelled"
        update_computeset.delay(cset)
        syslog.syslog(syslog.LOG_INFO, "Cancelling computeset job %s" % cset['name'])

    except OSError as e:
        cset["state"] = "failed"
        msg = "OSError: %s" % (e)
        update_computeset.delay(cset)
        syslog.syslog(syslog.LOG_ERR, msg)

    except CalledProcessError as e:
        cset["state"] = "failed"
        if e.returncode == 124:
            msg = "CalledProcessError: Timeout during request: %s" % (
                e.output.strip().rstrip())
        else:
            msg = "CalledProcessError: %s" % (e.output.strip().rstrip())
        update_computeset.delay(cset)
        syslog.syslog(syslog.LOG_ERR, msg)


@shared_task(ignore_result=True)
def update_computeset(cset_json):
    """ This task runs on comet-nucleus and can update the database """
    from api.models import ComputeSet
    from api import hostlist
    syslog.syslog(syslog.LOG_DEBUG, "update_computeset() running")

    try:
        cset = ComputeSet.objects.get(id=cset_json['id'])

        cset.jobid = cset_json["jobid"]

        if "name" in cset_json:
            cset.name = cset_json["name"]

        if "user" in cset_json:
            cset.user = cset_json["user"]

        if "account" in cset_json:
            cset.account = cset_json["account"]

        if "walltime_mins" in cset_json:
            cset.walltime_mins = cset_json["walltime_mins"]

        if "node_count" in cset_json:
            cset.node_count = cset_json["node_count"]

        if "start_time" in cset_json and not cset.start_time:
            cset.start_time = cset_json["start_time"]

        cset.save()

        # The following will only exist after jobscript barrier...
        if "nodelist" in cset_json:
            cset.nodelist = cset_json["nodelist"]
            cset.save()

        old_cset_state = None
        if "state" in cset_json:
            old_cset_state = cset.state
            if cset.state != cset_json["state"]:
                cset.state = cset_json["state"]
                cset.save()

            # Job passed from SUBMITTED to RUNNING state...
            if (old_cset_state == ComputeSet.CSET_STATE_SUBMITTED
                and cset.state == ComputeSet.CSET_STATE_RUNNING):
                if cset.nodelist is not None:
                    cset = ComputeSet.objects.get(pk=cset.id)
                    nodes = []
                    for compute in cset.computes.all():
                        nodes.append(compute.rocks_name)

                    hosts = hostlist.expand_hostlist("%s" % cset.nodelist)
                    # TODO: vlan & switchport configuration
                    poweron_nodeset.delay(nodes, hosts, None)

    except ComputeSet.DoesNotExist:
        cset = None
        msg = "update_computeset: %s" % (
            "ComputeSet (%d) does not exist" % (cset_json["id"]))
        syslog.syslog(syslog.LOG_ERR, msg)


@shared_task(ignore_result=True)
def poweron_nodeset(nodes, hosts, iso_name):
    syslog.syslog(syslog.LOG_DEBUG, "poweron_nodeset() running")
    if(hosts and (len(nodes) != len(hosts))):
        err ="poweron_nodest(): hosts length is not equal to nodes length"
        syslog.syslog(syslog.LOG_ERR, err)
        return
    outb = ""
    errb = ""

    if hosts:
        for node, host in zip(nodes, hosts):
            res = Popen(["/opt/rocks/bin/rocks", "set", "host", "vm", "%s" %
                         node, "physnode=%s" % host], stdout=PIPE, stderr=PIPE)
            out, err = res.communicate()
            outb += out
            errb += err

    if iso_name:
        (ret_code, out, err) = _attach_iso(nodes, iso_name)
        if ret_code:
            outb += out
            errb += err
            return "Error adding iso to nodes: %s\n%s" % (outb, errb)

    (ret_code, out, err) = _poweron_nodes(nodes)
    if ret_code:
        outb += out
        errb += err
        return "Error powering on nodes: %s\n%s" % (outb, errb)


@shared_task(ignore_result=True)
def poweroff_nodes(nodes, action):
    syslog.syslog(syslog.LOG_DEBUG, "poweroff_nodes() running")
    (ret_code, out, err) = _poweroff_nodes(nodes, action)
    if ret_code:
        syslog.syslog(syslog.LOG_ERR, err)
        return "%s\n%s" % (out, err)

# Local function to be called from multiple tasks


def _poweroff_nodes(nodes, action):
    args = ["/opt/rocks/bin/rocks", "stop", "host", "vm"]
    args.extend(nodes)
    args.append("action=%s" % action)
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return (res.returncode, out, err)


@shared_task(ignore_result=True)
def attach_iso(nodes, iso_name):
    syslog.syslog(syslog.LOG_DEBUG, "attach_iso() running")
    (ret_code, out, err) = _attach_iso(nodes, iso_name)
    if ret_code:
        syslog.syslog(syslog.LOG_ERR, err)
        return "%s\n%s" % (out, err)

# Local function to be called from multiple tasks


def _attach_iso(nodes, iso_name):
    args = ["/opt/rocks/bin/rocks", "set", "host", "vm", "cdrom"]
    args.extend(nodes)
    if iso_name:
        args.append("cdrom=%s/%s" % (ISOS_DIR, iso_name))
    else:
        args.append("cdrom=none")
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return (res.returncode, out, err)


@shared_task(ignore_result=True)
def poweron_nodes(nodes):
    syslog.syslog(syslog.LOG_DEBUG, "poweron_nodes() running")
    (ret_code, out, err) = _poweron_nodes(nodes)
    if ret_code:
        syslog.syslog(syslog.LOG_ERR, err)
        return "%s\n%s" % (out, err)

# Local function to be called from multiple tasks


def _poweron_nodes(nodes):
    args = ["/opt/rocks/bin/rocks", "start", "host", "vm"]
    args.extend(nodes)
    res = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = res.communicate()
    return (res.returncode, out, err)


@shared_task(ignore_result=True)
def update_clusters(clusters_json):
    from api.models import Cluster, Frontend, Compute, ComputeSet, FrontendInterface, ComputeInterface
    syslog.syslog(syslog.LOG_DEBUG, "update_clusters() running")
    for cluster_rocks in clusters_json:
        try:
            try:
                cluster_obj = Cluster.objects.get(
                    frontend__rocks_name=cluster_rocks["frontend"])

                if cluster_obj.vlan != cluster_rocks["vlan"]:
                    cluster_obj.vlan = cluster_rocks["vlan"]
                    cluster_obj.save()

                frontend = Frontend.objects.get(
                    rocks_name=cluster_rocks["frontend"])
                if(frontend.state != cluster_rocks["state"]
                    or frontend.memory != cluster_rocks["mem"]
                    or frontend.disksize != cluster_rocks["disksize"]
                    or frontend.cpus != cluster_rocks["cpus"]):
                    frontend.state = cluster_rocks["state"]
                    frontend.memory = cluster_rocks["mem"]
                    frontend.disksize = cluster_rocks["disksize"]
                    frontend.cpus = cluster_rocks["cpus"]
                    frontend.save()

                if(frontend.image_state != cluster_rocks["img_state"]
                    or frontend.image_locked != cluster_rocks["img_locked"]):
                    frontend.image_state = cluster_rocks["img_state"]
                    frontend.image_locked = cluster_rocks["img_locked"]
                    frontend.save()

                if frontend.gateway != cluster_rocks["gateway"]:
                    frontend.gateway = cluster_rocks["gateway"]
                    frontend.save()

            except Cluster.DoesNotExist:
                frontend = Frontend()
                frontend.name = cluster_rocks["frontend"]
                frontend.rocks_name = cluster_rocks["frontend"]
                frontend.state = cluster_rocks["state"]
                frontend.memory = cluster_rocks["mem"]
                frontend.disksize = cluster_rocks["disksize"]
                frontend.cpus = cluster_rocks["cpus"]
                frontend.type = cluster_rocks["type"]
                frontend.image_state = cluster_rocks["img_state"]
                frontend.image_locked = cluster_rocks["img_locked"]
                frontend.save()

                cluster_obj = Cluster()
                cluster_obj.name = cluster_rocks["frontend"]
                cluster_obj.vlan = cluster_rocks["vlan"]
                cluster_obj.frontend = frontend
                cluster_obj.save()

            cluster_obj = Cluster.objects.get(
                frontend__rocks_name=cluster_rocks["frontend"])
            frontend = Frontend.objects.get(rocks_name=cluster_rocks["frontend"])
            for interface in cluster_rocks['interfaces']:
                if interface["mac"]:
                    FrontendInterface.objects.update_or_create(
                        frontend=frontend, iface=interface["iface"], defaults={
                            'ip': interface["ip"],
                            'netmask': interface["netmask"],
                            'mac': interface["mac"], 
                            'iface': interface["iface"], 
                            'subnet': interface["subnet"]})

            for compute_rocks in cluster_rocks["computes"]:
                compute_obj, created = Compute.objects.get_or_create(
                    rocks_name=compute_rocks["name"], cluster=cluster_obj)
                if created:
                    compute_obj.name = compute_rocks["name"]
                    compute_obj.state = compute_rocks["state"]
                    compute_obj.memory = compute_rocks["mem"]
                    compute_obj.disksize = compute_rocks["disksize"]
                    compute_obj.cpus = compute_rocks["cpus"]
                    compute_obj.type = compute_rocks["type"]
                    compute_obj.image_state = compute_rocks["img_state"]
                    compute_obj.image_locked = compute_rocks["img_locked"]
                    compute_obj.save()
                else:
                    if(compute_obj.state != compute_rocks["state"]
                        or compute_obj.memory != compute_rocks["mem"]
                        or compute_obj.cpus != compute_rocks["cpus"]):
                        compute_obj.state = compute_rocks["state"]
                        compute_obj.memory = compute_rocks["mem"]
                        compute_obj.disksize = compute_rocks["disksize"]
                        compute_obj.cpus = compute_rocks["cpus"]
                        compute_obj.save()
                    if(compute_obj.image_state != compute_rocks["img_state"]
                        or compute_obj.image_locked != compute_rocks["img_locked"]):
                        compute_obj.image_state = compute_rocks["img_state"]
                        compute_obj.image_locked = compute_rocks["img_locked"]
                        compute_obj.save()

                for interface in compute_rocks['interfaces']:
                    if interface["mac"]:
                        ComputeInterface.objects.update_or_create(compute=compute_obj, iface=interface["iface"], 
                            defaults={ 
                                'ip': interface["ip"], 
                                'netmask': interface["netmask"], 
                                'mac': interface["mac"], 
                                'iface': interface["iface"], 
                                'subnet': interface["subnet"]})
        except:
            traceback.print_exc()
