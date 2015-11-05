from django.db import models
from rest_framework import serializers
import django.contrib.auth.models
from django.contrib.auth import get_user_model, authenticate

import subprocess

COMPUTESET_STATE_QUEUED = "queued"
COMPUTESET_STATE_COMPLETED = "completed"

# #################################################
#  CLUSTER
# #################################################

class Cluster(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(default="")
    project = models.ForeignKey(django.contrib.auth.models.Group)

    class Meta:
        managed = True


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
#  COMPUTE
# #################################################

class Compute(models.Model):
    name = models.CharField(max_length=128)
    rocks_name = models.CharField(max_length=128)
    cluster = models.ForeignKey(Cluster, related_name='computes')
    ip = models.GenericIPAddressField()
    memory = models.IntegerField()
    host = models.CharField(max_length=128)
    cpus = models.IntegerField()

    class Meta:
        managed = True

# #################################################
#  COMPUTESET
# #################################################

class ComputeSet(models.Model):
    state = models.CharField(max_length=128, default="queued")
    computes = models.ManyToManyField(Compute)
    cluster = models.ForeignKey(Cluster)

    #@classmethod
    #def create(cls):
    #    cset = cls()
    #    return cset
 

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



