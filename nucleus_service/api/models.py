from django.db import models
from rest_framework import serializers
import django.contrib.auth.models
from django.contrib.auth import get_user_model, authenticate

import subprocess

COMPUTESET_STATE_QUEUED = "queued"
COMPUTESET_STATE_COMPLETED = "completed"
COMPUTESET_STATE_STARTED = "started"

# #################################################
#  FRONTEND
# #################################################

class Frontend(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    rocks_name =  models.CharField(max_length=100, unique=True)
    cpus = models.IntegerField(null=True)
    memory = models.IntegerField(null=True)
    state = models.CharField(max_length=64, null=True)
    type = models.CharField(max_length=16)

    class Meta:
        managed = True

class FrontendInterface(models.Model):
    ip = models.GenericIPAddressField(default='0.0.0.0',null=True)
    mac = models.CharField(max_length=17,default='', unique=True)
    frontend = models.ForeignKey(Frontend, related_name='interface')
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
    host = models.CharField(max_length=128, null=True)
    cpus = models.IntegerField(null=True)
    memory = models.IntegerField(null=True)
    state = models.CharField(max_length=64, null=True)
    type = models.CharField(max_length=16)

    class Meta:
        managed = True

class ComputeInterface(models.Model):
    ip = models.GenericIPAddressField(default='0.0.0.0',null=True)
    mac = models.CharField(max_length=17,default='', unique=True)
    compute = models.ForeignKey(Compute, related_name='interface')
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


class NucleusUser(models.Model):
    key_name = models.CharField(max_length=128, primary_key=True)
    user = models.OneToOneField(django.contrib.auth.models.User, related_name='api_key')
    secret = models.TextField()

    class Meta:
        managed = True

class Nonce(models.Model):
    nonce = models.CharField(max_length=128, primary_key=True)
    timestamp = models.IntegerField()
    class Meta:
        managed = True
