from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import detail_route
from models import *
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import viewsets

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

    @asyncAction
    def list(self, request, format=None):
        """List the available clusters."""
        return list_clusters.delay()
            
    @asyncAction
    def retrieve(self, request, cluster_id=None, format=None):
        """Obtain details about the named cluster."""
        return list_clusters.delay(cluster_id)

    def destroy(self, request, cluster_id, format=None):
        """Destroy the named cluster."""
        return Response("destroy todo")

    @detail_route(methods=['post'])
    def stop(self, request, cluster_id, format=None):
        """Stop the named cluster."""
        return Response("stop todo")
    
    @detail_route(methods=['post'])
    def start(self, request, cluster_id, format=None):
        """Start the named cluster."""
        return Response("start todo")

# #################################################
#  COMPUTE
# #################################################

class ComputeViewSet(ModelViewSet):
    lookup_field = 'compute_id'
    serializer_class = ComputeSerializer

    def list(self, request, compute_id_cluster_id, format=None):
        """List the compute resources of the named cluster."""
        result = add.delay(1,3)
        res_ar = [v for v in result.collect()]
        return Response("todo %s"%res_ar)

    def retrieve(self, request, compute_id, compute_id_cluster_id, format=None):
        """Obtain the details of a named compute resource in a named cluster."""
        return Response("todo")

    def destroy(self, request, compute_id, compute_id_cluster_id, format=None):
        """Destroy the named compute resource in a named cluster."""
        return Response("todo")

    @detail_route(methods=['post'])
    def shutdown(self, request, compute_id, compute_id_cluster_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['post'])
    def reboot(self, request, compute_id, compute_id_cluster_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['post'])
    def reset(self, request, compute_id, compute_id_cluster_id, format=None):
        return Response("todo")
    
    @detail_route(methods=['post'])
    @asyncAction
    def poweron(self, request, compute_id_cluster_id, format=None):
        nodes = []
        hosts = []
        for obj in request.data:
            nodes.append(obj["node"])
            hosts.append(obj["host"])
        #compute_nodes = Compute(compute_id_cluster_id, compute_id)
        #res, err = compute_nodes.poweron()
        #job_id = random.randint(10000, 70000)
        #Group.create(job_id).save()
        #return Response("Done %s %s"%(nodes, hosts))
        return poweron_nodes.delay(nodes, hosts) 

    @detail_route(methods=['post'])
    def poweroff(self, request, compute_id, compute_id_cluster_id, format=None):
        """Power off the named compute resource in a named cluster.
        """        
        return Response("todo")
    
    def create(self, request, compute_id_cluster_id, format=None):
        """Create a new compute resource in a named cluster."""        
        # user = self.get_object(id)
        # serializer = UserSerializer(user, data=request.data)
        # if serializer.is_valid():
        #    serializer.save()
        #    return Response(serializer.data)
        #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response("todo")

# #################################################
#  GROUP
# #################################################

class GroupViewSet(ModelViewSet):
    lookup_field = 'group_id'
    serializer_class = GroupSerializer

    def list(self, request, group_id_cluster_id, format=None):
        """List the group resources of the named cluster."""
        return Response("todo")

    def retrieve(self, request, group_id, group_id_cluster_id, format=None):
        """Obtain the details of a named group resource in a named cluster."""
        group = Group(group_id_cluster_id, group_id)
        return Response(GroupSerializer(group).data)

    def destroy(self, request, group_id, group_id_cluster_id, format=None):
        """Destroy the named group resource in a named cluster."""
        return Response("todo")

# #################################################
#  FRONTEND
# #################################################
       
class FrontendViewSet(ModelViewSet):
    serializer_class = FrontendSerializer

    def retrieve(self, request, format=None):
        """Obtain the details of a frontend resource in a named cluster."""
        return Response("todo")

    @detail_route(methods=['post'])
    def shutdown(self, request, nested_1_cluster_id, format=None):
        """Shutdown the frontend of a named cluster."""
        return Response("todo")
    
    @detail_route(methods=['post'])
    def reboot(self, request, nested_1_cluster_id, format=None):
        """Reboot the frontend of a named cluster."""
        return Response("todo")
    
    @detail_route(methods=['post'])
    def reset(self, request, nested_1_cluster_id, format=None):
        """Reset the frontend of a named cluster."""
        return Response("todo")
    
    @detail_route(methods=['post'])
    def poweron(self, request, nested_1_cluster_id, format=None):
        """Power on the frontend of a named cluster."""
        return Response("todo")

    @detail_route(methods=['post'])
    def poweroff(self, request, nested_1_cluster_id, format=None):
        """Power off the frontend of a named cluster."""
        return Response("todo")

# #################################################
#  CLUSTERLIST
# #################################################

class ClusterList(APIView):
    """
    List all clusters, or create a new cluster.
    """
    def get(self, request, format=None):
        clusters = Cluster.objects.all()
        serializer = CLusterSerializer(clusters, many=True)
        return Response(serializer.data)
        
    def post(self, request, format=None):
        serializer = ClusterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

class UserViewSet(ModelViewSet):
    lookup_field = 'user_id'
    serializer_class = UserSerializer

    def list(self, request, format=None):
        """
        List all Persons that can create clusters.
        We will investigate djangos build in classes for that.
        """
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)
        return Response("todo")

    def retrieve(self, request, user_id, format=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)
        # return Response("todo")

    def destroy(self, request, user_id, format=None):
        return Response("todo")

# #################################################
#  PROJECT
# #################################################


class ProjectViewSet(ModelViewSet):
    lookup_field = 'project_id'
    serializer_class = ProjectSerializer

    def list(self, request, format=None):
        """
        List all Projects that can create clusters.
        We will investigate if django has already a project as part of user management.
        """
        queryset = Project.objects.all()
        serializer = ProjectSerializer(queryset, many=True)
        return Response(serializer.data)

        # return Response("todo")

    def retrieve(self, request, project_id, format=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)
        # return Response("todo")

    def destroy(self, request, project_id, format=None):
        return Response("todo")

# #################################################
#  CALL
# #################################################


class CallViewSet(ModelViewSet):
    lookup_field = 'call_id'
    serializer_class = CallSerializer

    def retrieve(self, request, call_id, format=None):
        call = Call.objects.get(pk=call_id)
        if(call.status < 1):
            serializer = self.serializer_class(call)
            return Response(serializer.data)

        if(call.url):
            location = call.url
        else:
            location = "/v1/call/%s/result"%(call_id)

        response = Response(
            "", 
            status=303,
            headers={'Location': location})
        return response
 

    @detail_route(methods=['get'])
    def result(self, request, call_id, format=None):
        call = Call.objects.get(pk=call_id)
        try:
            return Response(json.loads(call.data))
        except TypeError:
            return Response(call.data)
