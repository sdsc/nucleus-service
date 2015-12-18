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

class FrontendInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrontendInterface
        fields = ("ip", "mac")
        read_only_fields = ("ip", "mac")
        depth = 1

class FrontendSerializer(serializers.ModelSerializer):

    interface=FrontendInterfaceSerializer(many=True, read_only=True)
    class Meta:
        model = Frontend
        fields = ("name", "state", "memory", "cpus", "type", "interface")
        read_only_fields = ("state", "memory", "cpus", "type", "interface")
        depth = 1

class ComputeInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComputeInterface
        fields = ("ip", "mac")
        read_only_fields = ("ip", "mac")
        depth = 1

class ComputeSerializer(serializers.ModelSerializer):
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='name')
    interface=ComputeInterfaceSerializer(many=True, read_only=True)
    class Meta:
        model = Compute
        fields = ("name", "interface", "memory", "cpus", "cluster", "type", "state")
        read_only_fields = ("interface", "memory", "cpus", "cluster", "type", "state")
        depth = 1

class ComputeSetSerializer(serializers.ModelSerializer):
    computes=ComputeSerializer(many=True, read_only=True)
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='name')
    class Meta:
        model = ComputeSet
        fields = ['computes', 'id', 'state', 'cluster']
        read_only_fields = ('id', 'state', 'cluster')

class ComputeSetJobSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    computeset = serializers.SlugRelatedField(read_only=True, slug_field='id')
    name = serializers.CharField(max_length=64, allow_null=True)
    user = serializers.SlugRelatedField(read_only=True, slug_field='username')
    account = serializers.SlugRelatedField(read_only=True, slug_field='name')
    walltime_mins = serializers.IntegerField()
    nodelist = serializers.CharField(allow_null=True)
    state = serializers.ChoiceField(ComputeSetJob.CSETJOB_STATES)
    class Meta:
        model = ComputeSetJob
        fields = ['id', 'computeset', 'name', 'user', 'account', 'walltime_mins', 'nodelist', 'state']
        read_only_fields = ('id', 'computeset', 'name', 'user', 'account', 'walltime_mins', 'nodelist', 'state')

class ClusterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(default="")
    computes = ComputeSerializer(many=True, read_only=True)
    frontend = FrontendSerializer(read_only=True)
    project=serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = Cluster
        fields = ('name', 'description', 'computes', 'frontend', 'project')
        read_only_fields = ('computes', 'name', 'frontend')
