from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
import django.contrib.auth.models
from django.conf import settings

from models import *

# #################################################
#  USER
# #################################################

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name')
        read_only_fields = ('email', )

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = django.contrib.auth.models.Group
        fields = ['name']

class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ['name']

class FrontendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Frontend

class ComputeSerializer(serializers.ModelSerializer):
    #name = serializers.CharField(max_length=128)
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='fe_name')
    class Meta:
        model = Compute
        fields = ("name", "host", "ip", "memory", "cpus", "cluster")
        read_only_fields = ("ip", "memory", "cpus", "cluster")
        depth = 1

class ComputeSetSerializer(serializers.ModelSerializer):
    computes=ComputeSerializer(many=True, read_only=True)
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='fe_name')
    class Meta:
        model = ComputeSet
        fields = ['computes', 'id', 'state', 'cluster']
        read_only_fields = ('id', 'state', 'cluster')

class ClusterSerializer(serializers.ModelSerializer):
    fe_name = serializers.CharField(max_length=100)
    description = serializers.CharField(default="")
    computes = ComputeSerializer(many=True, read_only=True)
    project=serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = Cluster
        fields = ('fe_name', 'description', 'computes', 'project')
        read_only_fields = ('computes', 'fe_name')

class StoragepoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storagepool
        fields = ['name']

class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        #fields = ['name']
