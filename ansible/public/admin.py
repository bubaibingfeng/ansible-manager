
from django.contrib import admin
from public.models import *
import yaml
def writeini(master_ip='',node_ip=[]):
        data = "\n"
        data += '[master]\n' 
        data += '%s\n' % master_ip
        data += '[master-init]\n' 
        data += '%s\n' % master_ip
        data += '\n[node]\n'
        for n in node_ip:
            data += '%s\n' % n
        vs = Vars.objects.all()
        for v in vs:
            data += '[%s]\n' % v.varName
            data += 'ansible_ssh_pass=%s\n' % v.ssh_pass
            data += 'ansible_become_pass=%s\n' % v.ssh_pass
            data += 'ansible_ssh_port=%s\n' % v.ssh_port
            data += 'ansible_ssh_user=%s\n' % v.ssh_user
        data += '\n[k3s_cluster:children]\n'
        data += 'master-init\n'
        data += 'master\n'
        data += 'node\n'
        kvm=KVM.objects.all()
        for k in kvm:
            data += '\n[%s]\n' % k.vm_name
            data += '%s\n' % k.vm_ip
            data += '[%s:vars]\n' % k.vm_name
            data += 'ansible_ssh_pass=%s\n' % k.vm_ssh_pass
            data += 'ansible_ssh_port=%s\n' % k.vm_ssh_port
            data += 'ansible_ssh_user=%s\n' % k.vm_ssh_user
        vm=VM.objects.all()
        for k in vm:
            data += '\n[%s]\n' % k.vm_name
            data += '%s\n' % k.vm_ip
            data += '[%s:vars]\n' % k.vm_name
            data += 'ansible_ssh_pass=%s\n' % k.vm_ssh_pass
            data += 'ansible_ssh_port=%s\n' % k.vm_ssh_port
            data += 'ansible_ssh_user=%s\n' % k.vm_ssh_user
        with open(inventory, 'w') as f:
            f.write(data)
import json
import os
import subprocess

# 定义 IP 地址范围
ip_range_start = "192.168.1.100"
ip_range_end = "192.168.1.200"

# 将 IP 地址转化为数字
def ip_to_num(ip):
    parts = ip.split('.')
    return int(parts[0]) * 256**3 + int(parts[1]) * 256**2 + int(parts[2]) * 256 + int(parts[3])

# 将数值形式转为IP地址
def num_to_ip(num):
    return '.'.join([str((num >> (i * 8)) & 0xFF) for i in range(3, -1, -1)])

def is_ip_in_db(ip):
    # 检查 VM 和 KVM 表中的 vm_ip 和 kvm_ip 字段是否包含该 IP
    if VM.objects.filter(vm_ip=ip).exists() or KVM.objects.filter(vm_ip=ip).exists():
        print(f"{ip} is already in use in the database.")
        return True
    return False


# 检查IP是否可用 (通过ping)
def is_ip_available(ip):

    if is_ip_in_db(ip):
        return False  # IP 在数据库中已被使用，不可用 
    try:
        # 使用 ping 命令来检测 IP 是否可达，-c 1 表示发送一个 ICMP 回应包, -W 1 表示等待 1 秒超时
        output = subprocess.check_output(['ping', '-c', '1', '-W', '1', ip], stderr=subprocess.STDOUT, text=True)
        
        # 检查输出中是否包含 "Destination Host Unreachable" 字符串
        if "Destination Host Unreachable" in output:
            print(f"{ip} is unreachable, it might be available.")
            return True  # 目标主机不可达，认为是空闲 IP
        else:
            print(f"{ip} is reachable.")
            return False  # 目标主机可达，认为 IP 不空闲
    except subprocess.CalledProcessError as e:
        # 捕获 ping 失败的情况，判断输出是否有特定的 unreachable 错误
        if "Destination Host Unreachable" in e.output:
            print(f"{ip} is unreachable (exception), it might be available.")
            return True  # 目标主机不可达，认为是空闲 IP
        elif "Time to live exceeded" in e.output:
            print(f"{ip} is unreachable due to TTL exceeded. It's not considered available.")
            return False  # TTL exceeded，不认为 IP 是空闲的
        else:
            print(f"{ip} is  reachable due to another reason: {e.output}")
            return True  # 其他 ping 错误，认为该 IP 不可用（更严格的判断）
    except Exception as ex:
        print(f"Error occurred while pinging {ip}: {ex}")
        return False  # 如果发生其他错误，认为该 IP 不可用

# 查找可用的IP地址
def find_available_ip(start_ip, end_ip):
    start_num = ip_to_num(start_ip)
    end_num = ip_to_num(end_ip)
    
    for num in range(start_num, end_num + 1):
        ip = num_to_ip(num)
        if is_ip_available(ip):
            return ip

    raise Exception("No available IP addresses found.")




@admin.register(AnsiblePlaybooks)
class AnsiblePlaybooksAdmin(admin.ModelAdmin):
    list_display = ['nickName', 'playbook']

@admin.register(AnsibleTasks)    #
class AnsibleTasksAdmin(admin.ModelAdmin):
    list_display = [
            'AnsibleID',
            'CeleryID',
            'GroupName',
            'playbook',
            'ExtraVars',
            'AnsibleResult',
            'CeleryResult',
            'CreateTime'
            ]
# inventory 对应文件
from tools.config import inventory

# 主机列表修改内容


# 组列表相关内容

class VarsAdmin(admin.ModelAdmin):
    list_display = ['varName', 'ssh_pass', 'ssh_port', 'ssh_user']
# 重写 save_related 函数
    def save_related(self, request, form, formsets, change):
     super().save_related(request, form, formsets, change)
    # 在 admin 平台保存完对应关系之后，获取所有对应关系，保存到对应文件中
     if change:
        # 
        writeini()
admin.site.register(Vars, VarsAdmin)
@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display=['cluster_name','master_ip','node_ip']

@admin.register(KVM)
class KVMAdmin(admin.ModelAdmin):
    list_display=['vm_name','vm_ip','vm_ssh_user','vm_ssh_pass','vm_ssh_port']
    def save_related(self, request, form, formsets, change):
     super().save_related(request, form, formsets, change)
     if change:
        writeini()
@admin.register(VM)
class VMAdmin(admin.ModelAdmin):
    list_display=['vm_name','kvm_name','vm_ip','vm_ssh_user','vm_ssh_pass','vm_ssh_port']
    def save_related(self, request, form, formsets, change):
     super().save_related(request, form, formsets, change)
     if change:
        writeini()


