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
        fields = ("mac", "iface")
        read_only_fields = ("mac", "iface")
        depth = 1


class FrontendSerializer(serializers.ModelSerializer):

    interface = FrontendInterfaceSerializer(many=True, read_only=True)
    pub_ip = serializers.SerializerMethodField()
    frontend_state = serializers.SerializerMethodField()
    def get_pub_ip(self, frontend):
        try:
            return frontend.interface.exclude( iface="private" ).first().ip
        except FrontendInterface.DoesNotExist:
            return None

    def get_frontend_state(self, frontend):
        if(frontend.image_locked):
            return "syncing"
        if(frontend.image_state in ["unmapped", None]):
            return "ready"
        return "mapped"


    class Meta:
        model = Frontend
        fields = ("name", "state", "memory", "cpus", "disksize", "type", "interface", "pub_ip", "frontend_state")
        read_only_fields = ("state", "memory", "cpus", "disksize", "type", "interface", "pub_ip", "frontend_state")
        depth = 1


class ComputeInterfaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ComputeInterface
        fields = ("mac", "iface")
        read_only_fields = ("mac", "iface")
        depth = 1


class ComputeSerializer(serializers.ModelSerializer):
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='name')
    interface = ComputeInterfaceSerializer(many=True, read_only=True)
    active_computeset = serializers.SerializerMethodField()
    active_computeset_state = serializers.SerializerMethodField()
    compute_state = serializers.SerializerMethodField()

    def get_active_computeset(self, compute):
        try:
            return ComputeSet.objects.get(state__in=["created", "running", "submitted", "ending"], computes=compute.id).id
        except ComputeSet.DoesNotExist:
            return None

    def get_active_computeset_state(self, compute):
        try:
            return ComputeSet.objects.get(state__in=["created", "running", "submitted", "ending"], computes=compute.id).state
        except ComputeSet.DoesNotExist:
            return None

    def get_compute_state(self, compute):
        if(compute.image_locked):
            return "syncing"
        if(compute.image_state in ["unmapped", None]):
            return "ready"
        return "mapped"


    class Meta:
        model = Compute
        fields = ("name", "interface", "memory",
                  "cpus", "disksize", "cluster", "type", "state", "active_computeset", "active_computeset_state", "compute_state")
        read_only_fields = ("interface", "memory", "cpus",
                            "disksize", "cluster", "type", "state", "active_computeset", "active_computeset_state", "compute_state")
        depth = 1


class ComputeSetSerializer(serializers.ModelSerializer):
    computes = ComputeSerializer(many=True, read_only=True)
    cluster = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = ComputeSet
        fields = ['computes', 'id', 'state', 'cluster', 'account', 'walltime_mins', 'start_time']
        read_only_fields = ('computes', 'id', 'state', 'cluster', 'account', 'walltime_mins', 'start_time')


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
