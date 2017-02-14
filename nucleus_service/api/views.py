import hashlib
import json
import subprocess

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from tasks import poweron_nodes, poweroff_nodes
from tasks import submit_computeset, cancel_computeset, attach_iso
import hostlist
from models import Cluster, Compute, ComputeSet, Frontend
from serializers import ComputeSerializer, ComputeSetSerializer, FullComputeSetSerializer
from serializers import ClusterSerializer, FrontendSerializer, ProjectSerializer
from serializers import UserDetailsSerializer

import re, os, random, string, datetime
from django.db.models import Q

from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

# #################################################
#  CLUSTER
# #################################################


class ClusterViewSet(ModelViewSet):
    lookup_field = 'cluster_name'
    serializer_class = ClusterSerializer

    def get_queryset(self):
        """Obtain details about all clusters."""
        clusters = Cluster.objects.filter(
            project__in=self.request.user.groups.all())
        return clusters

    def retrieve(self, request, cluster_name, format=None):
        """Obtain details about the named cluster."""
        clust = get_object_or_404(Cluster, name=cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        serializer = ClusterSerializer(clust)
        return Response(serializer.data)

    def destroy(self, request, cluster_name, format=None):
        """Destroy the named cluster."""
        return Response("destroy todo")

# #################################################
#  COMPUTE
# #################################################


class ComputeViewSet(ViewSet):
    lookup_field = 'compute_name'

    serializer_class = ClusterSerializer

    def retrieve(self, request, compute_name_cluster_name, compute_name, format=None):
        """Obtain the details of a named compute resource in a named cluster."""
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        serializer = ComputeSerializer(compute)
        return Response(serializer.data)

    def destroy(self, request, compute_name_cluster_name, compute_name, format=None):
        """Destroy the named compute resource in a named cluster."""
        return Response("todo")

    @detail_route(methods=['put'])
    def shutdown(self, request, compute_name_cluster_name, compute_name, format=None):
        """Shutdown the named compute resource in a named cluster.
        """
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        if(not compute.computeset.filter(state=ComputeSet.CSET_STATE_RUNNING).exists()):
            return Response("Compute is not a member of an active computeset",
                            status=status.HTTP_400_BAD_REQUEST)

        poweroff_nodes.delay([compute.rocks_name], "shutdown")
        return Response(status=204)

    @detail_route(methods=['put'])
    def reboot(self, request, compute_name_cluster_name, compute_name, format=None):
        """Reboot the named compute resource in a named cluster.
        """
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        if(not compute.computeset.filter(state=ComputeSet.CSET_STATE_RUNNING).exists()):
            return Response("Compute is not a member of an active computeset",
                            status=status.HTTP_400_BAD_REQUEST)

        poweroff_nodes.delay([compute.rocks_name], "reboot")
        return Response(status=204)

    @detail_route(methods=['put'])
    def reset(self, request, compute_name_cluster_name, compute_name, format=None):
        """Reset the named compute resource in a named cluster.
        """
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        if(not compute.computeset.filter(state=ComputeSet.CSET_STATE_RUNNING).exists()):
            return Response("Compute is not a member of an active computeset",
                            status=status.HTTP_400_BAD_REQUEST)

        poweroff_nodes.delay([compute.rocks_name], "reset")
        return Response(status=204)

    @detail_route(methods=['put'])
    def poweroff(self, request, compute_name_cluster_name, compute_name, format=None):
        """Power off the named compute resource in a named cluster.
        """
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        if(not compute.computeset.filter(state=ComputeSet.CSET_STATE_RUNNING).exists()):
            return Response("Compute is not a member of an active computeset",
                            status=status.HTTP_400_BAD_REQUEST)

        poweroff_nodes.delay([compute.rocks_name], "poweroff")
        return Response(status=204)

    @detail_route(methods=['put'])
    def poweron(self, request, compute_name_cluster_name, compute_name, format=None):
        """Power on the named compute resource in a named cluster.
        """
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        if(not compute.computeset.filter(state=ComputeSet.CSET_STATE_RUNNING).exists()):
            return Response("Compute is not a member of an active computeset",
                            status=status.HTTP_400_BAD_REQUEST)

        poweron_nodes.delay([compute.rocks_name])
        return Response(status=204)

    @detail_route(methods=['put'])
    def attach_iso(self, request, compute_name_cluster_name, compute_name, format=None):
        """Attach an ISO to the named compute resource in a named cluster.
        """
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        if not "iso_name" in request.GET:
            return Response("Please provide the iso_name", status=400)
        attach_iso.delay([compute.rocks_name], request.GET["iso_name"])
        return Response(status=204)

    @detail_route(methods=['post'])
    def rename(self, request, compute_name_cluster_name, compute_name, format=None):
        """Rename the named compute resource in a named cluster.
        """
        compute = get_object_or_404(
            Compute, name=compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        new_name = request.data.get("name")
        if(not re.match('^[a-zA-Z0-9_-]+$',new_name)):
            return Response("New name can opnly contain alphanumeric symbols, digits and '-_'.",
                            status=status.HTTP_400_BAD_REQUEST)

        compute.name = new_name
        compute.save()
        return Response(status=204)


# #################################################
#  CONSOLE
##################################################

def get_console(request, console_compute_name, nucleus_name=None, is_frontend=False):
    """Open VNC console to named resource."""
    resp = "Success"
    sleep_time = 15

    from xml.dom.minidom import parse, parseString
    import libvirt

    if(is_frontend):
        compute = Frontend.objects.get(rocks_name=console_compute_name)
    else:
        compute = Compute.objects.get(rocks_name=console_compute_name)

    physical_host = compute.physical_host

    if(not physical_host):
        return Response("The VM is not running",
                        status=status.HTTP_400_BAD_REQUEST)

    hypervisor = libvirt.open("qemu+tls://%s.comet/system?pkipath=/var/secrets/cometvc" %
                              physical_host)
    domU = hypervisor.lookupByName(compute.name)

    # Grab the current XML definition of the domain...
    flags = libvirt.VIR_DOMAIN_XML_SECURE
    domU_xml = parseString(domU.XMLDesc(flags))

    # Parse out the <graphics>...</graphics> device node...
    for gd in domU_xml.getElementsByTagName('graphics'):
        xml = gd.toxml()

    duration = 3600
    password = ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase +
            string.ascii_lowercase +
            string.digits) for _ in range(16))

    # Generate a new passwdValidTo string...
    dt1 = datetime.datetime.utcnow()
    dt2 = dt1 + datetime.timedelta(0, int(duration))
    timestr = dt2.strftime("%Y-%m-%dT%H:%M:%S")

    # Modify the passwd and passwdValidUntil fields...
    gd.setAttribute('passwd', password)
    gd.setAttribute('passwdValidTo', timestr)

    port = gd.getAttribute("port")

    # Apply the change to the domain...
    flags = libvirt.VIR_DOMAIN_DEVICE_MODIFY_FORCE | \
        libvirt.VIR_DOMAIN_DEVICE_MODIFY_LIVE
    retval = domU.updateDeviceFlags(gd.toxml(), flags)

    cmd = ['/usr/bin/sudo',
           '-u',
           'nucleus_comet',
           '/opt/nucleus-scripts/bin/open_tunnel.py',
           '-H',
           '{hostname}'.format(hostname=physical_host),
           '-p',
           '{hostport}'.format(hostport=port),
           '-s',
           '{duration}'.format(duration=sleep_time)]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    except OSError as e:
        resp = "Execution failed: %s" % (e)
        return Response(resp)

    tun_port = ''

    tun_port = proc.stdout.readline().strip()
    url_base = "/nucleus-guacamole-0.9.8/index.html?hostname=localhost"
    url = request.build_absolute_uri("%s&port=%s&token=%s&host=%s" % (url_base, tun_port, password, nucleus_name))
    response = Response(
        url,
        status=303,
        headers={'Location': url})
    return response

class ConsoleViewSet(ViewSet):
    """Open VNC console to named compute resource."""
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, compute_name_cluster_name, console_compute_name, format=None):
        compute = get_object_or_404(
            Compute, name=console_compute_name, cluster__name=compute_name_cluster_name)
        if not compute.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        return get_console(request, compute.rocks_name, console_compute_name)


class FrontendConsoleViewSet(ViewSet):
    """Open VNC console to name frontend resource."""
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, console_cluster_name, format=None):
        clust = get_object_or_404(Cluster, name=console_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        return get_console(request, clust.frontend.rocks_name, console_cluster_name, True)


##################################################
#  COMPUTESET
# #################################################

class ComputeSetViewSet(ModelViewSet):
    lookup_field = 'computeset_id'
    serializer_class = ComputeSetSerializer

    def get_queryset(self):
        """Obtain the details of all ComputeSets."""
        cset = ComputeSet.objects.filter(
            cluster__project__in=self.request.user.groups.all())

        states = self.request.GET.getlist('state')
        #state = self.request.query_params.get('state', None)
        if states:
            cset = cset.filter(state__in=states)
        return cset

    def retrieve(self, request, computeset_id, format=None):
        """Obtain the details of the identified ComputeSet."""
        cset = get_object_or_404(ComputeSet, pk=computeset_id)
        if not cset.cluster.project in request.user.groups.all():
            raise PermissionDenied()
        serializer = ComputeSetSerializer(cset)
        return Response(serializer.data)

    @detail_route(methods=['put'])
    def poweroff(self, request, computeset_id, format=None):
        """Power off the identified ComputeSet."""
        cset = ComputeSet.objects.get(pk=computeset_id)
        if not cset.cluster.project in request.user.groups.all():
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)

        poweroff_nodes.delay(computes, "poweroff")

        cancel_computeset.delay(FullComputeSetSerializer(cset).data)

        return Response(status=204)

    def poweron(self, request, format=None):
        """ Power on a set of computes creating a ComputeSet."""
        clust = get_object_or_404(Cluster, name=request.data["cluster"])
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()

        walltime_mins = request.data.get("walltime_mins")
        if not walltime_mins:
            walltime_mins = 2880

        nodes = []
        hosts = []

        if request.data.get("computes"):
            if request.data["computes"] is list:
                for obj in request.data["computes"]:
                    nodes.append(obj["name"])
                    hosts.append(obj["host"])
            else:
                nodes = hostlist.expand_hostlist("%s" % request.data["computes"])
                if request.data.get("hosts"):
                    hosts = hostlist.expand_hostlist("%s" % request.data["hosts"])
        elif request.data.get("count"):
            computes_selected = Compute.objects.filter(cluster=clust).exclude(
                    computeset__state__in=[
                        ComputeSet.CSET_STATE_CREATED,
                        ComputeSet.CSET_STATE_SUBMITTED,
                        ComputeSet.CSET_STATE_RUNNING,
                        ComputeSet.CSET_STATE_ENDING]
                ).exclude(state="active").filter(Q(image_state="unmapped") | Q(image_state__isnull=True)).exclude(image_locked=True)[:int(request.data["count"])]
            nodes.extend([comp.name for comp in computes_selected])
            if(len(nodes) < int(request.data["count"]) or int(request.data["count"]) == 0):
                return Response("There are %i nodes available for starting. Requested number should be greater than zero."%len(nodes),
                                status=status.HTTP_400_BAD_REQUEST)

        if hosts and len(nodes) != len(hosts):
            return Response("The length of hosts should be equal to length of nodes",
                            status=status.HTTP_400_BAD_REQUEST)

        cset = ComputeSet()
        cset.cluster = clust
        cset.user = clust.username
        if(request.data.get("allocation")):
            cset.account = request.data["allocation"]
        elif(clust.allocations.count() == 1):
            cset.account = clust.allocations.get().allocation
        else:
            return Response("Please specify the allocation",
                    status=status.HTTP_400_BAD_REQUEST)

        if(not clust.allocations.filter(allocation=cset.account).exists()):
            return Response("Allocation %s does not belong to the cluster."%cset.account,
                    status=status.HTTP_400_BAD_REQUEST)
        cset.walltime_mins = walltime_mins
        cset.jobid = None
        cset.name = None
        cset.nodelist = ""
        cset.state = ComputeSet.CSET_STATE_CREATED
        cset.node_count = len(nodes)
        cset.save()

        for node in nodes:
            compute = Compute.objects.get(name=node, cluster=clust)

            other_cs_query = ComputeSet.objects.filter(computes__id__exact=compute.id).exclude(
                state__in=[ComputeSet.CSET_STATE_COMPLETED, ComputeSet.CSET_STATE_FAILED, ComputeSet.CSET_STATE_CANCELLED])
            if other_cs_query.exists():
                cset.delete()
                err_cs = other_cs_query.get()
                return Response("The compute %s belongs to computeset %s which is in %s state" % (node, err_cs.id, err_cs.state), status=status.HTTP_400_BAD_REQUEST)

            if (compute.image_state not in ["unmapped", None]) or compute.image_locked:
                cset.delete()
                return Response("The node %s's image is in %s state and image locked status is %s. Please contact the user support if the VM is not running." %(node, compute.image_state, compute.image_locked), status=status.HTTP_400_BAD_REQUEST)

            if compute.cluster.name != request.data["cluster"]:
                cset.delete()
                return Response("The node %s does not belong to the cluster %s, belongs to %s" % (node, request.data["cluster"], compute.cluster.name), status=status.HTTP_400_BAD_REQUEST)

            cset.computes.add(compute)

        submit_computeset.delay(FullComputeSetSerializer(cset).data)

        # We should only poweron computes after entering jobscript and
        # finishing the PROLOG on all allocated nodes. At that point the
        # nodelist will be returned and we can call poweron_nodeset()
        #poweron_nodeset.delay(nodes, hosts)

        location = "/nucleus/v1/computeset/%s" % (cset.id)

        serializer = ComputeSetSerializer(cset)
        response = Response(
            serializer.data,
            status=201,
            headers={'Location': request.build_absolute_uri(location)})

        return response

    @detail_route(methods=['put'])
    def shutdown(self, request, computeset_id, format=None):
        """Shutdown the nodes in the identified ComputeSet."""
        cset = ComputeSet.objects.get(pk=computeset_id)
        if not cset.cluster.project in request.user.groups.all():
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)
            if compute.cluster.name != request.data["cluster"]:
                cset.delete()
                return Response("The node %s does not belong to the cluster %s, belongs to %s" % (node, request.data["cluster"], compute.cluster.name), status=status.HTTP_400_BAD_REQUEST)

            cset.computes.add(compute)

        submit_computeset.delay(FullComputeSetSerializer(cset).data)

        # We should only poweron computes after entering jobscript and
        # finishing the PROLOG on all allocated nodes. At that point the
        # nodelist will be returned and we can call poweron_nodeset()
        #poweron_nodeset.delay(nodes, hosts)

        location = "/nucleus/v1/computeset/%s" % (cset.id)

        serializer = ComputeSetSerializer(cset)
        response = Response(
            serializer.data,
            status=201,
            headers={'Location': request.build_absolute_uri(location)})

        return response

    @detail_route(methods=['put'])
    def shutdown(self, request, computeset_id, format=None):
        """Shutdown the nodes in the identified ComputeSet."""
        cset = ComputeSet.objects.get(pk=computeset_id)
        if not cset.cluster.project in request.user.groups.all():
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)
            if compute.cluster.name != request.data["cluster"]:
                cset.delete()
                return Response("The node %s does not belong to the cluster %s, belongs to %s" % (node, request.data["cluster"], compute.cluster.name), status=status.HTTP_400_BAD_REQUEST)

            cset.computes.add(compute)

        submit_computeset.delay(FullComputeSetSerializer(cset).data)

        # We should only poweron computes after entering jobscript and
        # finishing the PROLOG on all allocated nodes. At that point the
        # nodelist will be returned and we can call poweron_nodeset()
        #poweron_nodeset.delay(nodes, hosts)

        location = "/nucleus/v1/computeset/%s" % (cset.id)

        serializer = ComputeSetSerializer(cset)
        response = Response(
            serializer.data,
            status=201,
            headers={'Location': request.build_absolute_uri(location)})

        return response

    @detail_route(methods=['put'])
    def shutdown(self, request, computeset_id, format=None):
        """Shutdown the nodes in the identified ComputeSet."""
        cset = ComputeSet.objects.get(pk=computeset_id)
        if not cset.cluster.project in request.user.groups.all():
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)

        poweroff_nodes.delay(computes, "shutdown")

        cancel_computeset.delay(FullComputeSetSerializer(cset).data)

        return Response(status=204)

    @detail_route(methods=['put'])
    def reboot(self, request, computeset_id, format=None):
        """Reboot the nodes in the identified ComputeSet."""
        cset = ComputeSet.objects.get(pk=computeset_id)
        if not cset.cluster.project in request.user.groups.all():
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)

        poweroff_nodes.delay(computes, "reboot")

        return Response(status=204)

    @detail_route(methods=['put'])
    def reset(self, request, computeset_id, format=None):
        """Reset the nodes in the identified ComputeSet."""
        cset = ComputeSet.objects.get(pk=computeset_id)
        if not cset.cluster.project in request.user.groups.all():
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)

        poweroff_nodes.delay(computes, "reset")

        return Response(status=204)

# #################################################
#  FRONTEND
# #################################################


class FrontendViewSet(ViewSet):

    def retrieve(self, request, frontend_cluster_name, format=None):
        """Obtain the details of a frontend resource in a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        serializer = FrontendSerializer(clust.frontend)
        return Response(serializer.data)

    @detail_route(methods=['put'])
    def shutdown(self, request, frontend_cluster_name, format=None):
        """Shutdown the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "shutdown")
        return Response(status=204)

    @detail_route(methods=['put'])
    def reboot(self, request, frontend_cluster_name, format=None):
        """Reboot the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "reboot")
        return Response(status=204)

    @detail_route(methods=['put'])
    def reset(self, request, frontend_cluster_name, format=None):
        """Reset the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "reset")
        return Response(status=204)

    @detail_route(methods=['put'])
    def poweron(self, request, frontend_cluster_name, format=None):
        """Power on the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        poweron_nodes.delay([clust.frontend.rocks_name])
        return Response(status=204)

    @detail_route(methods=['put'])
    def poweroff(self, request, frontend_cluster_name, format=None):
        """Power off the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "poweroff")
        return Response(status=204)

    @detail_route(methods=['put'])
    def attach_iso(self, request, frontend_cluster_name, format=None):
        """Attach an ISO to the frontendresource in a named cluster.
        """
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if not clust.project in request.user.groups.all():
            raise PermissionDenied()
        if not "iso_name" in request.GET:
            return Response("Please provide the iso_name", status=400)
        attach_iso.delay([clust.frontend.rocks_name], request.GET["iso_name"])
        return Response(status=204)


# #################################################
#  USER
# #################################################


class UserDetailsView(RetrieveUpdateAPIView):

    """
    Returns User's details in JSON format.

    Accepts the following GET parameters: token
    Accepts the following POST parameters:
        Required: token
        Optional: email, first_name, last_name and UserProfile fields
    Returns the updated UserProfile and/or User object.
    """
    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


# #################################################
#  PROJECT
# #################################################


class ProjectListView(ListAPIView):
    """Returns project details."""
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return self.request.user.groups.all()


class ImageUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def get(self, request, format=None):
        filepath = '/mnt/images/public'
        return Response(["public/%s"%dir for dir in os.listdir(filepath)])

    def post(self, request, format=None):
        file_obj = request.FILES['file']
        try:
            filepath = '/mnt/images/public/%s' % (file_obj.name)
            if not request.META.get('HTTP_MD5'):
                return Response("md5 was not provided", status=400)

            if request.META['HTTP_MD5'] != md5_for_file(file_obj.chunks()):
                return Response("md5 does not match the file", status=400)

            with open(filepath, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            return Response(status=204)
        finally:
            if(file_obj):
                file_obj.close()


def md5_for_file(chunks):
    md5 = hashlib.md5()
    for data in chunks:
        md5.update(data)
    return md5.hexdigest()
