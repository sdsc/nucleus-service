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


from django.shortcuts import get_object_or_404

from api.tasks import poweron_nodeset, poweron_nodes, poweroff_nodes
import random

from functools import wraps

from celery.exceptions import TimeoutError
from celery.result import AsyncResult
import time
import json


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
        return Response(None)
    
    @detail_route(methods=['put'])
    def reboot(self, request, compute_name_cluster_name, compute_name, format=None):
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([compute.rocks_name], "reboot")
        return Response(None)
    
    @detail_route(methods=['put'])
    def reset(self, request, compute_name_cluster_name, compute_name, format=None):
        return Response("todo")
    
    @detail_route(methods=['put'])
    def poweroff(self, request, compute_name_cluster_name, compute_name, format=None):
        """Power off the named compute resource in a named cluster.
        """        
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([compute.rocks_name], "poweroff")
        return Response(None)

    @detail_route(methods=['put'])

    def poweron(self, request, compute_name_cluster_name, compute_name, format=None):
        """Power on the named compute resource in a named cluster.
        """        
        compute = get_object_or_404(Compute, name=compute_name, cluster__name = compute_name_cluster_name)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        poweron_nodes.delay([compute.rocks_name])
        return Response(None)
    

# #################################################
#  CONSOLE
# #################################################

class ConsoleViewSet(ViewSet):
    def retrieve(self, request, compute_name_cluster_name, console_compute_name, format=None):
        return Response("todo")

# #################################################
#  COMPUTESET
# #################################################

class ComputeSetViewSet(ModelViewSet):
    lookup_field = 'computeset_id'
    serializer_class = ComputeSetSerializer

    def get_queryset(self):
        cset = ComputeSet.objects.filter(cluster__project__in=self.request.user.groups.all())
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
        cset.state = COMPUTESET_STATE_COMPLETED
        cset.save()
        serializer = ComputeSetSerializer(cset)
        return Response(serializer.data)

    def poweron(self, request, format=None):
        """ Power on a set of nodes """
        clust = get_object_or_404(Cluster, name=request.data["cluster"])
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()

        cset = ComputeSet()
        cset.cluster = clust
        cset.save()

        nodes = []
        hosts = []
        for obj in request.data["computes"]:
            compute = Compute.objects.get(name=obj["name"])

            other_cs_query = ComputeSet.objects.filter(computes__id__exact=compute.id).exclude(state__exact = COMPUTESET_STATE_COMPLETED)
            if(other_cs_query.exists()):
                cset.delete()
                err_cs = other_cs_query.get()
                return Response("The compute %s belongs to computeset %s which is in %s state"%(obj["name"], err_cs.id, err_cs.state), status=status.HTTP_400_BAD_REQUEST)

            if(compute.cluster.name != request.data["cluster"]):
                cset.delete()
                return Response("The node %s does not belong to the cluster %s, belongs to %s"%(obj["name"], request.data["cluster"], compute.cluster.name), status=status.HTTP_400_BAD_REQUEST)

            nodes.append(obj["name"])
            hosts.append(obj["host"])
            cset.computes.add(compute)
        cset.state = "started"
        cset.save()

        poweron_nodeset.delay(nodes, hosts)

        location = "/nucleus/v1/computeset/%s"%(cset.id)

        response = Response(
            None, 
            status=303,
            headers={'Location': location})
        return response

    @detail_route(methods=['put'])
    def shutdown(self, request, computeset_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['put'])
    def reboot(self, request, computeset_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['put'])
    def reset(self, request, computeset_id, format=None):
        return Response("todo")
    
# #################################################
#  FRONTEND
# #################################################
       
class FrontendViewSet(ViewSet):
    #serializer_class = FrontendSerializer

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
        return Response(None)
    
    @detail_route(methods=['put'])
    def reboot(self, request, frontend_cluster_name, format=None):
        """Reboot the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "reboot")
        return Response(None)
    
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
        return Response(None)

    @detail_route(methods=['put'])
    def poweroff(self, request, frontend_cluster_name, format=None):
        """Power off the frontend of a named cluster."""
        clust = get_object_or_404(Cluster, name=frontend_cluster_name)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        poweroff_nodes.delay([clust.frontend.rocks_name], "poweroff")
        return Response(None)

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

