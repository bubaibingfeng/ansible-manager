from django.db import models

class AnsibleTasks(models.Model):
    AnsibleID          = models.CharField(max_length=80,unique=True, null=True,blank=True)
    CeleryID         = models.CharField(max_length=80,unique=True, null=True,blank=True)
    GroupName         = models.CharField(max_length=80, null=True,blank=True)
    playbook         = models.CharField(max_length=80, null=True,blank=True)
    ExtraVars         = models.TextField(blank=True, null=True)
    AnsibleResult     = models.TextField(blank=True)
    CeleryResult      = models.TextField(blank=True)
    CreateTime      = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    class Meta:
        ordering = ['id']
    def __str__(self):
        return self.AnsibleID

from django.db import models
from django.contrib.auth.models import User

# 存储 playbook 的名称和文件路径
class AnsiblePlaybooks(models.Model):
    nickName     = models.CharField(max_length=80,null=True,blank=True)
    playbook     = models.CharField(max_length=80,unique=True, null=True,blank=False)
    def __str__(self):
        return self.playbook

# 我们添加了 TaskUser 字段，使用了一对多的关系 models.ForeignKey
class AnsibleTasks(models.Model):
    AnsibleID          = models.CharField(max_length=80,unique=True, null=True,blank=True)
    CeleryID         = models.CharField(max_length=80,unique=True, null=True,blank=True)
    TaskUser        =  models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    GroupName         = models.CharField(max_length=80, null=True,blank=True)
    playbook         = models.CharField(max_length=80, null=True,blank=True)
    ExtraVars         = models.TextField(blank=True, null=True)
    AnsibleResult     = models.TextField(blank=True)
    CeleryResult      = models.TextField(blank=True)
    CreateTime      = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    class Meta:
        ordering = ['id']
        verbose_name_plural = "任务列表"
        verbose_name="任务列表"
    def __str__(self):
        return self.AnsibleID

class Vars(models.Model):
    varName = models.CharField(max_length=80,unique=True)
    ssh_pass = models.CharField(max_length=80)
    ssh_port = models.CharField(max_length=80)
    ssh_user = models.CharField(max_length=80)

    def __str__(self):
        return self.varName

class Cluster(models.Model):
    cluster_name = models.CharField(max_length=80,unique=True)
    master_ip = models.CharField(max_length=80,unique=True)
    node_ip = models.JSONField(max_length=80)
    ntp_server= models.CharField(max_length=80,default='172.20.134.10')
    def __str__(self):
        return self.master_ip

class VM(models.Model):
    vm_name = models.CharField(max_length=80,unique=True)
    kvm_name = models.CharField(max_length=80)
    vm_ip = models.CharField(max_length=80)
    vm_ssh_user = models.CharField(max_length=80)
    vm_ssh_pass = models.CharField(max_length=80)
    vm_ssh_port = models.CharField(max_length=80)
    vm_cpu = models.CharField(max_length=80)
    vm_memory = models.CharField(max_length=80)
    vm_disk = models.CharField(max_length=80)
    vm_ip_reachable = models.BooleanField(default=False)  # 新增字段，默认不可达
    vm_useable = models.BooleanField(default=True)  # 新增字段，默认可用
    def __str__(self):
        return self.vm_name



class KVM(models.Model):    
    vm_name = models.CharField(max_length=80,unique=True)
    vm_ip = models.CharField(max_length=80)
    vm_ssh_user = models.CharField(max_length=80)
    vm_ssh_pass = models.CharField(max_length=80)
    vm_ssh_port = models.CharField(max_length=80)
    vm_ip_reachable = models.BooleanField(default=False)  # 新增字段，默认不可达

    def __str__(self):
        return self.vm_name

class State(models.Model):
    vm_name = models.CharField(max_length=80,unique=True)
    vm_cpu_usage = models.CharField(max_length=80,default='暂无数据,请10s后重新刷新')
    vm_memory_usage = models.CharField(max_length=80,default='暂无数据')
    vm_disk_usage = models.CharField(max_length=80,default='暂无数据')
    update_time = models.CharField(max_length=80,default='暂无数据')
