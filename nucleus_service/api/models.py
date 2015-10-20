from django.db import models
from rest_framework import serializers
import django.contrib.auth.models
from django.contrib.auth import get_user_model, authenticate

import subprocess

# #################################################
#  PROJECT
# #################################################

class Project(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

# #################################################
#  STORAGE
# #################################################

class Storage(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

# #################################################
#  FRONTEND
# #################################################

class Frontend(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    #name = models.CharField(max_length=100)

    class Meta:
        pass

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

# #################################################
#  COMPUTE
# #################################################

class Compute(object):
    def __init__(self, cluster_id, compute_id):
        self.name = compute_id

    def poweron(self):
        out, err = subprocess.Popen(['ssh', 'dimm@comet-fe1', '/opt/rocks/bin/rocks start host vm %s'%self.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return [out, err]
        

# #################################################
#  CLUSTER
# #################################################

class Cluster(models.Model):
    fe_name = models.CharField(max_length=100)
    description = models.TextField(default="")
    project = models.ForeignKey(django.contrib.auth.models.Group)

    class Meta:
        managed = True


# #################################################
#  STORAGEPOOL
# #################################################

class Storagepool(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)
        
# #################################################
#  CALL
# #################################################

class Call(models.Model):
        CALL_STATUS = (
            (0, 'In progress'),
            (1, 'Done'),
            (2, 'Error')
        )

        created = models.DateTimeField(auto_now_add=True)
        updated = models.DateTimeField(auto_now=True)
        status = models.IntegerField(choices=CALL_STATUS)
        call_id = models.CharField(max_length=128, primary_key=True)
        data = models.TextField()
        url = models.CharField(max_length=256, null=True)



