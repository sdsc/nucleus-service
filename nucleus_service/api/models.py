from django.db import models
from rest_framework import serializers
import django.contrib.auth.models
from django.contrib.auth import get_user_model, authenticate

import subprocess

COMPUTESET_STATE_QUEUED = "queued"
COMPUTESET_STATE_COMPLETED = "completed"

# #################################################
#  FRONTEND
# #################################################

class Frontend(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    rocks_name =  models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=64, null=True)
    type = models.CharField(max_length=16)

    class Meta:
        managed = True

# #################################################
#  CLUSTER
# #################################################

class Cluster(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(default="")
    project = models.ForeignKey(django.contrib.auth.models.Group, null = True)
    frontend = models.ForeignKey(Frontend, related_name='cluster')

    class Meta:
        managed = True

# #################################################
#  COMPUTE
# #################################################

class Compute(models.Model):
    name = models.CharField(max_length=128)
    rocks_name = models.CharField(max_length=128, unique=True)
    cluster = models.ForeignKey(Cluster, related_name='computes')
    ip = models.GenericIPAddressField(null=True)
    memory = models.IntegerField(null=True)
    host = models.CharField(max_length=128, null=True)
    cpus = models.IntegerField(null=True)
    state = models.CharField(max_length=64, null=True)
    type = models.CharField(max_length=16)

    class Meta:
        managed = True

# #################################################
#  COMPUTESET
# #################################################

class ComputeSet(models.Model):
    state = models.CharField(max_length=128, default="queued")
    computes = models.ManyToManyField(Compute)
    cluster = models.ForeignKey(Cluster)

    class Meta:
        managed = True


