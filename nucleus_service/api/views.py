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
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, RetrieveAPIView


from django.shortcuts import get_object_or_404

from api.tasks import list_clusters, poweron_nodes
import random

from functools import wraps

from celery.exceptions import TimeoutError
from celery.result import AsyncResult
import time
import json


def asyncAction(f):
     @wraps(f)
     def wrapper(*args, **kwds):
        result = f(*args, **kwds)
        if(isinstance(result, AsyncResult)):
            cur_call, created = Call.objects.get_or_create(status=0, call_id = result.id)
            response = Response(
              None, 
                status=202,
                headers={'Location': "/v1/call/%s"%(result.id)})
            return response
     return wrapper

# #################################################
#  CLUSTER
# #################################################
       
class ClusterViewSet(ModelViewSet):
    lookup_field = 'cluster_id'
    serializer_class = ClusterSerializer

    def get_queryset(self):
        clusters = Cluster.objects.filter(project__in=self.request.user.groups.all())
        return clusters

    #@asyncAction
    def retrieve(self, request, cluster_id, format=None):
        """Obtain details about the named cluster."""
        clust = get_object_or_404(Cluster, name=cluster_id)
        if(not clust.project in request.user.groups.all()):
            raise PermissionDenied()
        #return list_clusters.delay([cluster_id])
        serializer = ClusterSerializer(clust)
        return Response(serializer.data)

    def destroy(self, request, cluster_id, format=None):
        """Destroy the named cluster."""
        return Response("destroy todo")

# #################################################
#  COMPUTE
# #################################################

class ComputeViewSet(ViewSet):
    lookup_field = 'compute_id'

    serializer_class = ClusterSerializer
    def retrieve(self, request, compute_id_cluster_id, compute_id, format=None):
        """Obtain the details of a named compute resource in a named cluster."""
        compute = get_object_or_404(Compute, name=compute_id)
        if(not compute.cluster.project in request.user.groups.all()):
            raise PermissionDenied()
        serializer = ComputeSerializer(compute)
        return Response(serializer.data)

    def destroy(self, request, compute_id_cluster_id, compute_id, format=None):
        """Destroy the named compute resource in a named cluster."""
        return Response("todo")

    @detail_route(methods=['put'])
    def shutdown(self, request, compute_id_cluster_id, compute_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['put'])
    def reboot(self, request, compute_id_cluster_id, compute_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['put'])
    def reset(self, request, compute_id_cluster_id, compute_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['put'])
    def poweroff(self, request, compute_id_cluster_id, compute_id, format=None):
        """Power off the named compute resource in a named cluster.
        """        
        return Response("todo")
    @detail_route(methods=['put'])

    def poweron(self, request, compute_id_cluster_id, compute_id, format=None):
        """Power on the named compute resource in a named cluster.
        """        
        return Response("todo")
    

# #################################################
#  CONSOLE
# #################################################

class ConsoleViewSet(ViewSet):
    def retrieve(self, request, compute_id_cluster_id, console_compute_id, format=None):
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

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! poweron_nodes.delay(nodes, hosts)

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
       
class FrontendViewSet(ModelViewSet):
    serializer_class = FrontendSerializer

    def retrieve(self, request, format=None):
        """Obtain the details of a frontend resource in a named cluster."""
        return Response("todo")

    @detail_route(methods=['put'])
    def shutdown(self, request, frontend_cluster_id, format=None):
        """Shutdown the frontend of a named cluster."""
        return Response("todo")
    
    @detail_route(methods=['put'])
    def reboot(self, request, frontend_cluster_id, format=None):
        """Reboot the frontend of a named cluster."""
        return Response("todo")
    
    @detail_route(methods=['put'])
    def reset(self, request, frontend_cluster_id, format=None):
        """Reset the frontend of a named cluster."""
        return Response("todo")
    
    @detail_route(methods=['put'])
    def poweron(self, request, frontend_cluster_id, format=None):
        """Power on the frontend of a named cluster."""
        return Response("todo")

    @detail_route(methods=['put'])
    def poweroff(self, request, frontend_cluster_id, format=None):
        """Power off the frontend of a named cluster."""
        return Response("todo")

# #################################################
# CLUSTERDETAIL
# #################################################

class ClusterDetail(APIView):
    """
    Retrieve, update or delete a cluster instance.
    """
    def get_object(self, id):
        try:
           return Cluster.objects.get(id=id)
        except Cluster.DoesNotExist:
           raise Http404

    def start(self, id):
        return Response("start")
    
    def get(self, request, id, format=None):
        cluster = self.get_object(id)
        serializer = ClusterSerializer(cluster)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def shutdown(self, request, compute_id, compute_id_cluster_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['post'])
    def reset(self, request, compute_id, compute_id_cluster_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['post'])
    def start(self, request, compute_id, compute_id_cluster_id, format=None):
        return Response("todo")

    @detail_route(methods=['post'])
    def stop(self, request, compute_id, compute_id_cluster_id, format=None):
        return Response("todo")

# #################################################
#  STORAGE
# #################################################

class StorageViewSet(ModelViewSet):
    lookup_field = 'storage_id'
    serializer_class = StorageSerializer

    def list(self, request,
             compute_id_cluster_id,
             storage_id_compute_id,
             format=None):
        return Response("todo")

    def retrieve(self, request,
                 storage_id,
                 compute_id_cluster_id,
                 storage_id_compute_id,
                 format=None):
        return Response("todo")

    def destroy(self, request,
                storage_id,
                compute_id_cluster_id,
                storage_id_compute_id,
                format=None):
        return Response("todo")

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

