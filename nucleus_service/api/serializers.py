from django.contrib.auth import get_user_model
import django.contrib.auth.models
from rest_framework import serializers

from models import Cluster, Frontend, FrontendInterface, Compute, ComputeInterface, ComputeSet

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
        fields = ("ip", "netmask", "mac", "iface", "subnet")
        read_only_fields = ("ip", "netmask", "mac", "iface", "subnet")
        depth = 1


class FrontendSerializer(serializers.ModelSerializer):

    interface = FrontendInterfaceSerializer(many=True, read_only=True)

    class Meta:
        model = Frontend
        fields = ("name", "state", "memory", "cpus", "disksize", "type", "interface")
        read_only_fields = ("state", "memory", "cpus", "disksize", "type", "interface")
        depth = 1


class ComputeInterfaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ComputeInterface
        fields = ("ip", "netmask", "mac", "iface", "subnet")
        read_only_fields = ("ip", "netmask", "mac", "iface", "subnet")
        depth = 1


class ComputeSerializer(serializers.ModelSerializer):
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='name')
    interface = ComputeInterfaceSerializer(many=True, read_only=True)

    class Meta:
        model = Compute
        fields = ("name", "interface", "memory",
                  "cpus", "disksize", "cluster", "type", "state")
        read_only_fields = ("interface", "memory", "cpus",
                            "disksize", "cluster", "type", "state")
        depth = 1


class ComputeSetSerializer(serializers.ModelSerializer):
    computes = ComputeSerializer(many=True, read_only=True)
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = ComputeSet
        fields = ['computes', 'id', 'state', 'cluster']
        read_only_fields = ('computes', 'id', 'state', 'cluster')


class FullComputeSetSerializer(serializers.ModelSerializer):
    computes = ComputeSerializer(many=True, read_only=True)
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = ComputeSet
        fields = ['computes', 'id', 'state', 'cluster', 'user', 'account',
                  'walltime_mins', 'jobid', 'name', 'nodelist', 'state', 'node_count']
        read_only_fields = ('computes', 'id', 'state', 'cluster', 'user', 'account',
                            'walltime_mins', 'jobid', 'name', 'nodelist', 'state', 'node_count')


class ClusterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(default="")
    computes = ComputeSerializer(many=True, read_only=True)
    frontend = FrontendSerializer(read_only=True)
    project = serializers.SlugRelatedField(read_only=True, slug_field='name')
    allocations = serializers.SlugRelatedField(read_only=True, slug_field='allocation', many='True')

    class Meta:
        model = Cluster
        fields = ('name', 'description', 'computes',
                  'frontend', 'project', 'vlan', 'allocations')
        read_only_fields = ('computes', 'name', 'frontend', 'vlan', 'allocations')
