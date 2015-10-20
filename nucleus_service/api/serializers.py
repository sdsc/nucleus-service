from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
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
        model = Project
        fields = ['name']

class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ['name']

class FrontendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Frontend

class GroupSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    state = serializers.CharField(max_length=100)

class ComputeSerializer(serializers.Serializer):
    pass

class ClusterSerializer(serializers.ModelSerializer):
    fe_name = serializers.CharField(max_length=100)
    description = serializers.CharField(default="")

    class Meta:
        model = Cluster
        fields = ('fe_name', 'description')

class StoragepoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storagepool
        fields = ['name']

class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        #fields = ['name']
