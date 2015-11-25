from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import DetailView, ListView
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import detail_route
from models import *
from serializers import *
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, RetrieveAPIView

import subprocess

from django.shortcuts import get_object_or_404

from api.tasks import poweron_nodeset, poweron_nodes, poweroff_nodes
import random

from functools import wraps

from celery.exceptions import TimeoutError
from celery.result import AsyncResult
import time
import json
import hostlist
import os,sys

# #################################################
#  CLUSTER
# #################################################
       
class ClusterViewSet(ModelViewSet):
    lookup_field = 'cluster_name'
    serializer_class = ClusterSerializer

    def get_queryset(self):
        clusters = Cluster.objects.filter(project__in=self.request.user.groups.all())
        return clusters

    def retrieve(self, request, cluster_name, format=None):
        """Obtain details about the named cluster."""
        clust = get_object_or_404(Cluster, name=cluster_name)
        if(not clust.project in request.user.groups.all()):
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
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        serializer = ComputeSerializer(compute)
        return Response(serializer.data)

    def destroy(self, request, compute_name_cluster_name, compute_name, format=None):
        """Destroy the named compute resource in a named cluster."""
        return Response("todo")

    @detail_route(methods=['put'])
    def shutdown(self, request, compute_name_cluster_name, compute_name, format=None):
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([compute.rocks_name], "shutdown")
        return Response(status=204)
    
    @detail_route(methods=['put'])
    def reboot(self, request, compute_name_cluster_name, compute_name, format=None):
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([compute.rocks_name], "reboot")
        return Response(status=204)
    
    @detail_route(methods=['put'])
    def reset(self, request, compute_name_cluster_name, compute_name, format=None):
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([compute.rocks_name], "reset")
        return Response(status=204)
    
    @detail_route(methods=['put'])
    def poweroff(self, request, compute_name_cluster_name, compute_name, format=None):
        """Power off the named compute resource in a named cluster.
        """        
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([compute.rocks_name], "poweroff")
        return Response(status=204)

    @detail_route(methods=['put'])

    def poweron(self, request, compute_name_cluster_name, compute_name, format=None):
        """Power on the named compute resource in a named cluster.
        """        
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweron_nodes.delay([compute.rocks_name])
        return Response(status=204)
    

# #################################################
#  CONSOLE
##################################################

def get_console(console_compute_name):
    resp = "Success"
    sleep_time = 15

    # Set random VNC password for guest valid for sleep_time
    cmd = ['/usr/bin/sudo',
            '-u',
            'nucleus_comet',
            '/home/nucleus_comet/bin/set_vnc_passwd.py',
            '-G',
            '{guest}'.format(guest=console_compute_name),
            '-s',
            '{duration}'.format(duration=sleep_time)]
    try:
            retcode = subprocess.call(cmd)
            if retcode < 0:
                    resp = "Child was terminated by signal %d" % (-retcode)
                    return Response(resp)

    except OSError as e:
            resp = "Execution failed: %s" % (e)
            return Response(resp)


    # Get VNC connection params...
    cmd = ['/usr/bin/sudo',
            '-u',
            'nucleus_comet',
            '/home/nucleus_comet/bin/get_vnc_params.py',
            '-G',
            '{guest}'.format(guest=console_compute_name)]
    try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    except OSError as e:
            resp = "Execution failed: %s" % (e)
            return Response(resp)

    params = ''
    for line in iter(proc.stdout.readline,''):
            import re
            params += line.rstrip().strip()

    vnc_conn = json.loads(params)[0]["vnc"][0]
    (phys_host, passwd, port) = (vnc_conn["phys-host"], vnc_conn["password"], vnc_conn["port"])

    
    # Open tunnel from localhost -> phys-host:port...
    cmd = ['/usr/bin/sudo',
            '-u',
            'nucleus_comet',
            '/home/nucleus_comet/bin/open_tunnel.py',
            '-H',
            '{hostname}'.format(hostname=phys_host),
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
    url_base = "https://comet-nucleus.sdsc.edu/nucleus-guacamole/index.html?hostname=localhost"
    url = "%s&port=%s&password=%s" % (url_base, tun_port, passwd)

    response = Response(
        url,
        status=303,
        headers={'Location': url})
    return response

class ConsoleViewSet(ViewSet):
    def retrieve(self, request, compute_name_cluster_name, console_compute_name, format=None):
        compute = get_object_or_404(Compute, name=console_compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        return get_console(console_compute_name)

class FrontendConsoleViewSet(ViewSet):
    def retrieve(self, request, console_cluster_name, format=None):
        clust = get_object_or_404(Cluster, name=console_cluster_name)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        return get_console(clust.frontend.rocks_name)


##################################################
#  COMPUTESET
# #################################################

class ComputeSetViewSet(ModelViewSet):
    lookup_field = 'computeset_id'
    serializer_class = ComputeSetSerializer

    def get_queryset(self):
        cset = ComputeSet.objects.filter(cluster__project__in=self.request.user.groups.all())

        state = self.request.query_params.get('state', None)
        if state is not None:
            cset = cset.filter(state=state)
        return cset

    def retrieve(self, request, computeset_id, format=None):
        cset = get_object_or_404(ComputeSet, pk=computeset_id)
        if(not cset.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        serializer = ComputeSetSerializer(cset)
        return Response(serializer.data)

    @detail_route(methods=['put'])
    def poweroff(self, request, computeset_id, format=None):
        """Power off the named nodeset."""        
        cset = ComputeSet.objects.get(pk=computeset_id)
        if(not cset.cluster.project in request.user.groups.all()):
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)

        poweroff_nodes.delay(computes, "poweroff")

        return Response(status=204)

    def poweron(self, request, format=None):
        """ Power on a set of nodes """
        clust = get_object_or_404(Cluster, name=request.data["cluster"])
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()


        nodes = []
        hosts = []

        if(request.data["computes"] is list):
            for obj in request.data["computes"]:
                nodes.append(obj["name"])
                hosts.append(obj["host"])
        else:
            nodes = hostlist.expand_hostlist("%s"%request.data["computes"])
            if(request.data.get("hosts")):
                hosts = hostlist.expand_hostlist("%s"%request.data["hosts"])

        if(hosts and len(nodes) != len(hosts)):
            return Response("The length of hosts should be equal to length of nodes", status=status.HTTP_400_BAD_REQUEST)
            
        cset = ComputeSet()
        cset.cluster = clust
        cset.save()

        for node in nodes:
            compute = Compute.objects.get(name=node, cluster=clust)

            other_cs_query = ComputeSet.objects.filter(computes__id__exact=compute.id).exclude(state__exact = COMPUTESET_STATE_COMPLETED)
            if(other_cs_query.exists()):
                cset.delete()
                err_cs = other_cs_query.get()
                return Response("The compute %s belongs to computeset %s which is in %s state"%(node, err_cs.id, err_cs.state), status=status.HTTP_400_BAD_REQUEST)

            if(compute.cluster.name != request.data["cluster"]):
                cset.delete()
                return Response("The node %s does not belong to the cluster %s, belongs to %s"%(node, request.data["cluster"], compute.cluster.name), status=status.HTTP_400_BAD_REQUEST)

            cset.computes.add(compute)

        cset.state = COMPUTESET_STATE_QUEUED
        cset.save()

        poweron_nodeset.delay(nodes, hosts)

        location = "/nucleus/v1/computeset/%s"%(cset.id)

        serializer = ComputeSetSerializer(cset)

        response = Response(
            serializer.data,
            status=201,
            headers={'Location': location})
        return response

    @detail_route(methods=['put'])
    def shutdown(self, request, computeset_id, format=None):
        cset = ComputeSet.objects.get(pk=computeset_id)
        if(not cset.cluster.project in request.user.groups.all()):
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)

        poweroff_nodes.delay(computes, "shutdown")

        return Response(status=204)

    @detail_route(methods=['put'])
    def reboot(self, request, computeset_id, format=None):
        cset = ComputeSet.objects.get(pk=computeset_id)
        if(not cset.cluster.project in request.user.groups.all()):
            raise PermissionDenied()

        computes = []
        for compute in cset.computes.all():
            computes.append(compute.rocks_name)

        poweroff_nodes.delay(computes, "reboot")

        return Response(status=204)
    
    @detail_route(methods=['put'])
    def reset(self, request, computeset_id, format=None):
        cset = ComputeSet.objects.get(pk=computeset_id)
        if(not cset.cluster.project in request.user.groups.all()):
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
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        serializer = FrontendSerializer(clust.frontend)
        return Response(serializer.data)

    @detail_route(methods=['put'])
    def shutdown(self, request, frontend_cluster_name, format=None):
        """Shutdown the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "shutdown")
        return Response(status=204)
    
    @detail_route(methods=['put'])
    def reboot(self, request, frontend_cluster_name, format=None):
        """Reboot the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "reboot")
        return Response(status=204)
    
    @detail_route(methods=['put'])
    def reset(self, request, frontend_cluster_name, format=None):
        """Reset the frontend of a named cluster."""
        return Response("todo")
    
    @detail_route(methods=['put'])
    def poweron(self, request, frontend_cluster_name, format=None):
        """Power on the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        poweron_nodes.delay([clust.frontend.rocks_name])
        return Response(status=204)

    @detail_route(methods=['put'])
    def poweroff(self, request, frontend_cluster_name, format=None):
        """Power off the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "poweroff")
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
    serializer_class = ProjectSerializer
    def get_queryset(self):
        return self.request.user.groups.all()

