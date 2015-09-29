from django.db import models
from rest_framework import serializers

import subprocess

# #################################################
#  USER
# #################################################

class User(models.Model):
    username = models.CharField(max_length=24)
    created = models.DateTimeField(auto_now_add=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.CharField(max_length=100)            

    class Meta:
        ordering = ('username',)
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username',
                  'firstname',
                  'lastname',
                  'email',
                  'created']

# #################################################
#  PROJECT
# #################################################

class Project(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name']

# #################################################
#  STORAGE
# #################################################

class Storage(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ['name']

# #################################################
#  FRONTEND
# #################################################

class Frontend(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    #name = models.CharField(max_length=100)

    class Meta:
        pass

class FrontendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Frontend

# #################################################
#  GROUP
# #################################################

class Group(models.Model):
    group_id = models.IntegerField()
    state = models.CharField(max_length=100, default="queued")

    @classmethod
    def create(cls, group_id):
        group = cls(group_id=group_id, state="running")
        return group

    class Meta:
        managed = True

class GroupSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    state = serializers.CharField(max_length=100)

# #################################################
#  COMPUTE
# #################################################

class Compute(object):
    def __init__(self, cluster_id, compute_id):
        self.name = compute_id

    def poweron(self):
        out, err = subprocess.Popen(['ssh', 'dimm@comet-fe1', '/opt/rocks/bin/rocks start host vm %s'%self.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return [out, err]
        

class ComputeSerializer(serializers.Serializer):
    pass

# #################################################
#  CLUSTER
# #################################################

class Cluster(models.Model):
    fe_name = models.CharField(max_length=100,default="")
    vlan = models.IntegerField(default=0)
    fe_pub_ip = models.CharField(max_length=45,default="0.0.0.0")
    fe_pub_gateway = models.CharField(max_length=45,default="0.0.0.0")
    fe_container = models.CharField(max_length=100,default="comet-ln1")
    num_computes = models.IntegerField(default=3)
    compute_containers = models.CharField(max_length=255,default="")
    fe_cdrom = models.CharField(max_length=255,default="none")

    class Meta:
        managed = True

class ClusterSerializer(serializers.ModelSerializer):
    fe_name = serializers.CharField(max_length=100,default="")
    vlan = serializers.IntegerField(default=0)
    fe_pub_ip = serializers.CharField(max_length=45,default="0.0.0.0")
    fe_pub_gateway = serializers.CharField(max_length=45,default="0.0.0.0")
    fe_container = serializers.CharField(max_length=100,default="comet-ln1")
    num_computes = serializers.IntegerField(default=3)
    compute_containers = serializers.CharField(max_length=255,default="")
    fe_cdrom = serializers.CharField(max_length=255,default="none")

    class Meta:
        model = Cluster

# #################################################
#  STORAGEPOOL
# #################################################

class Storagepool(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)
        
class StoragepoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storagepool
        fields = ['name']
