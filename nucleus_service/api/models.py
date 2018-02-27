import django.contrib.auth.models
from django.db import models

# #################################################
#  FRONTEND
# #################################################


class Frontend(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    rocks_name = models.CharField(max_length=100, unique=True)
    physical_host = models.CharField(max_length=100, null=True)
    cpus = models.IntegerField(null=True)
    memory = models.IntegerField(null=True)
    disksize = models.IntegerField(null=True)
    image_state = models.CharField(max_length=30, null=True)
    image_locked = models.NullBooleanField()
    state = models.CharField(max_length=64, null=True)
    gateway = models.GenericIPAddressField(default='0.0.0.0', null=True)
    dns1 = models.GenericIPAddressField(default='132.249.20.25', null=True)
    dns2 = models.GenericIPAddressField(default='198.202.75.26', null=True)
    ntp = models.GenericIPAddressField(default='132.249.20.25', null=True)
    type = models.CharField(max_length=16)

    class Meta:
        managed = True


class FrontendInterface(models.Model):
    ip = models.GenericIPAddressField(default='0.0.0.0', null=True)
    netmask = models.GenericIPAddressField(default='0.0.0.0', null=True)
    mac = models.CharField(max_length=60, default='', unique=True)
    iface = models.CharField(max_length=64, default='')
    subnet = models.CharField(max_length=64, null=True)
    frontend = models.ForeignKey(Frontend, related_name='interface', on_delete=models.CASCADE)

    class Meta:
        managed = True

# #################################################
#  CLUSTER
# #################################################


class Cluster(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(default="")
    project = models.ForeignKey(django.contrib.auth.models.Group, null=True, on_delete=models.CASCADE)
    frontend = models.ForeignKey(Frontend, related_name='cluster', on_delete=models.CASCADE)
    vlan = models.IntegerField(null=True)
    username = models.CharField(max_length=128, null=False) # username under which we run the VMs for the cluster

    class Meta:
        managed = True

class Allocation(models.Model):
    allocation = models.CharField(max_length=128, unique=True)
    cluster = models.ManyToManyField(Cluster, related_name="allocations")

# #################################################
#  COMPUTE
# #################################################


class Compute(models.Model):
    name = models.CharField(max_length=128)
    rocks_name = models.CharField(max_length=128, unique=True)
    physical_host = models.CharField(max_length=100, null=True)
    cluster = models.ForeignKey(Cluster, related_name='computes', on_delete=models.CASCADE)
    host = models.CharField(max_length=128, null=True)
    cpus = models.IntegerField(null=True)
    disksize = models.IntegerField(null=True)
    image_state = models.CharField(max_length=30, null=True)
    image_locked = models.NullBooleanField()
    memory = models.IntegerField(null=True)
    state = models.CharField(max_length=64, null=True)
    type = models.CharField(max_length=16)

    class Meta:
        managed = True
        unique_together = (("name", "cluster"),)

class ComputeInterface(models.Model):
    ip = models.GenericIPAddressField(default='0.0.0.0', null=True)
    netmask = models.GenericIPAddressField(default='0.0.0.0', null=True)
    mac = models.CharField(max_length=60, default='', unique=True)
    compute = models.ForeignKey(Compute, related_name='interface', on_delete=models.CASCADE)
    iface = models.CharField(max_length=64, default='')
    subnet = models.CharField(max_length=64, null=True)

    class Meta:
        managed = True
        unique_together = (("iface", "compute"))

# #################################################
#  NUCLEUSUSER
# #################################################


class NucleusUser(models.Model):
    key_name = models.CharField(max_length=128, primary_key=True)
    user = models.OneToOneField(
        django.contrib.auth.models.User, related_name='api_key')
    secret = models.TextField()

    class Meta:
        managed = True

# #################################################
#  NONCE
# #################################################


class Nonce(models.Model):
    nonce = models.CharField(max_length=128, primary_key=True)
    timestamp = models.IntegerField()

    class Meta:
        managed = True

# #################################################
#  COMPUTESET
# #################################################


class ComputeSet(models.Model):
    CSET_STATE_CREATED = 'created'
    CSET_STATE_SUBMITTED = 'submitted'
    CSET_STATE_FAILED = 'failed'
    CSET_STATE_RUNNING = 'running'
    CSET_STATE_CANCELLED = 'cancelled'
    CSET_STATE_ENDING = 'ending'
    CSET_STATE_COMPLETED = 'completed'
    CSET_STATES = (
        (CSET_STATE_CREATED, 'Created'),
        (CSET_STATE_SUBMITTED, 'Submitted'),
        (CSET_STATE_FAILED, 'Failed'),
        (CSET_STATE_RUNNING, 'Running'),
        (CSET_STATE_CANCELLED, 'Cancelled'),
        (CSET_STATE_ENDING, 'Ending'),
        (CSET_STATE_COMPLETED, 'Completed'),
    )
    created = models.DateTimeField(auto_now_add=True)
    computes = models.ManyToManyField(Compute, related_name='computeset')
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    jobid = models.PositiveIntegerField(unique=True, null=True)
    name = models.CharField(max_length=64, unique=True, null=True)
    user = models.CharField(max_length=30)
    account = models.CharField(max_length=80)
    reservation = models.CharField(max_length=80, null=True)
    walltime_mins = models.PositiveIntegerField()
    nodelist = models.TextField(null=True)
    node_count = models.PositiveIntegerField(null=True)
    state = models.CharField(max_length=128,
                             choices=CSET_STATES,
                             default=CSET_STATE_CREATED)
    start_time = models.PositiveIntegerField(null=True)

    class Meta:
        managed = True
