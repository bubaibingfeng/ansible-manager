# 导入必须的模块
from django.http import HttpResponse
import redis

html = '''<!DOCTYPE html>
<html lang="zh-CN">
  <head><link href="https://cdn.jsdelivr.net/npm/bootstrap@3.3.7/dist/css/bootstrap.min.css" rel="stylesheet"></head>
  <div class="col-md-3"></div><div class="col-md-6">%s</div><div class="col-md-3"></div>
'''

def redis_info(request):
    r = redis.Redis(host="127.0.0.1", port=6379)
    data = r.info()
    msg = ""
    for i,j in data.items():
        msg += '<tr><td >%s</td><td>%s</td></tr>' % (i, j)
    table ='<div><table class="table table-bordered">%s</table></div>' % msg
    return HttpResponse(html % table)

from django.shortcuts import render
from django.http import JsonResponse

# 函数 index 至少需要传入一个参数， 返回时 render 需要传入三个参数，第一个为函数传入值，第二个为 html 模板文件，第三个为字典数据，会在模板中使用
def index(request):
    return render(request, 'public_base.html', {})
# JsonResponse 会返回一个 json 字符串
def jsdata(request):
    return JsonResponse({'msg': 'this is a JsonResponse return'})

from django.views.generic import ListView
from django.views.generic import DetailView
from public.models import *
from django.core.serializers import serialize
import json


import os
import subprocess
import django

# 设置 Django 项目的环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name.settings')
django.setup()


def is_ip_reachable(ip):
    try:
        # 使用 ping 命令来检测 IP 是否可达， -c 1 表示发送一个 ICMP 回应包, -W 1 表示等待 1 秒超时
        output = subprocess.check_output(['ping', '-c', '1', '-W', '1', ip], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

# 函数：更新所有虚拟机的 IP 可达状态
def update_vm_ip_reachability():
    vms = VM.objects.all()  # 获取所有虚拟机
    for vm in vms:
        ip_reachable = is_ip_reachable(vm.vm_ip)  # 检查是否可达
        vm.vm_ip_reachable = ip_reachable  # 更新字段
        vm.save()  # 保存更改
        print(f"Updated VM {vm.vm_name}: IP reachable - {ip_reachable}")
def update_kvm_ip_reachability():
    vms = KVM.objects.all()  # 获取所有虚拟机
    for vm in vms:
        ip_reachable = is_ip_reachable(vm.vm_ip)  # 检查是否可达
        vm.vm_ip_reachable = ip_reachable  # 更新字段
        vm.save()  # 保存更改
        print(f"Updated VM {vm.vm_name}: IP reachable - {ip_reachable}")



# 我们继承 ListView 类，指定 model 为 AnsibleTasks (models 文件中的 class 数据对象)，这个会查询 AnsibleTasks 所有数据，并将数据与模板文件 templates/public/ansibletasks_list.html 匹配返回 http 请求
class AnsibleTaskList(ListView):
    model = AnsibleTasks

    # def render_to_response(self, context, **response_kwargs):
    #     tasks = self.get_queryset()
    #     data = json.loads(serialize('json', tasks))
        
    #     # 如果你想自定义返回的字段，可以这样处理：
    #     simplified_data = []
    #     for item in data:
    #         simplified_data.append({
    #             'id': item['pk'],
    #             'name': item['fields']['name'],
    #             'status': item['fields']['status'],
    #             # 添加其他你想要包含的字段
    #         })
        
    #     return JsonResponse(simplified_data, safe=False)
# 继承 DetailView 类，指定 model 为 AnsibleTasks
class AnsibleTaskDetail(DetailView):
    model = AnsibleTasks
class KVMList(ListView):
    model = KVM
    def render_to_response(self, context, **response_kwargs):
        update_kvm_ip_reachability()
        tasks = self.get_queryset()  
        data = json.loads(serialize('json', tasks))
    
        # 如果你想自定义返回的字段，可以这样处理：
        simplified_data = []
        for item in data:
            simplified_data.append({
                'vm_name': item['fields']['vm_name'],
                'vm_ip': item['fields']['vm_ip'],
                'vm_ip_reachable' : item['fields']['vm_ip_reachable'],
                # 添加其他你想要包含的字段
            })
        
        return JsonResponse(simplified_data, safe=False)
        
class KVMDetailView(DetailView):
    model = KVM
    slug_field = 'vm_name'
    slug_url_kwarg = 'vm_name'

    def render_to_response(self, context, **response_kwargs):
        kvm = self.get_object()
        data = json.loads(serialize('json', [kvm]))[0]
        
        simplified_data = {
            'vm_name': data['fields']['vm_name'],
            'vm_ip': data['fields']['vm_ip'],
            'vm_ssh_user': data['fields']['vm_ssh_user'],
            'vm_ssh_pass': data['fields']['vm_ssh_pass'],
            'vm_ssh_port': data['fields']['vm_ssh_port']
            # 添加其他你想要包含的字段
        }
        
        return JsonResponse(simplified_data)
class KVMList2(ListView):
    model = KVM

class KVMDetail(DetailView):
    model = KVM
    # def render_to_response(self, context, **response_kwargs):
    #     kvm = self.get_object()
    #     data = {
    #         'id': kvm.id,
    #         'vm_name': kvm.vm_name,
    #         'vm_ip': kvm.vm_ip,
    #         'vm_ssh_user': kvm.vm_ssh_user,
    #         'vm_ssh_pass': kvm.vm_ssh_pass,
    #         'vm_ssh_port': kvm.vm_ssh_port,
    #         # 添加其他你想要包含的字段
    #     }
    #     return JsonResponse(data)
class VMList(ListView):
    model = VM
    def render_to_response(self, context, **response_kwargs):
        update_vm_ip_reachability()
        tasks = self.get_queryset()
        data = json.loads(serialize('json', tasks))       
        # 如果你想自定义返回的字段，可以这样处理：
        simplified_data = []
        for item in data:
            simplified_data.append({
                'kvm_name': item['fields']['kvm_name'],
                'vm_name': item['fields']['vm_name'],
                'vm_ip': item['fields']['vm_ip'],
                'vm_ip_reachable' : item['fields']['vm_ip_reachable'],
                'vm_useable' : item['fields']['vm_useable'],
                # 添加其他你想要包含的字段
            })
        
        return JsonResponse(simplified_data, safe=False)

class VMDetailView(DetailView):
    model = VM
    slug_field = 'vm_name'
    slug_url_kwarg = 'vm_name'

    def render_to_response(self, context, **response_kwargs):
        vm = self.get_object()
        data = json.loads(serialize('json', [vm]))[0]
        
        simplified_data = {
            'kvm_name': data['fields']['kvm_name'],
            'vm_name': data['fields']['vm_name'],
            'vm_ip': data['fields']['vm_ip'],
            'vm_ssh_user': data['fields']['vm_ssh_user'],
            'vm_ssh_pass': data['fields']['vm_ssh_pass'],
            'vm_ssh_port': data['fields']['vm_ssh_port']
            # 添加其他你想要包含的字段
        }
        
        return JsonResponse(simplified_data)


class ClusterList(ListView):
    model = Cluster
    def render_to_response(self, context, **response_kwargs):
        update_kvm_ip_reachability()
        tasks = self.get_queryset()  
        data = json.loads(serialize('json', tasks))
    
        # 如果你想自定义返回的字段，可以这样处理：
        simplified_data = []
        for item in data:
            simplified_data.append({
                'cluster_name': item['fields']['cluster_name'],
                'master_ip': item['fields']['master_ip'],
                'node_ip' : item['fields']['node_ip'],
                # 添加其他你想要包含的字段
            })
        
        return JsonResponse(simplified_data, safe=False)


class ClusterDetailView(DetailView):
    model = Cluster
    slug_field = 'cluster_name'
    slug_url_kwarg = 'cluster_name'

    def render_to_response(self, context, **response_kwargs):
        cluster = self.get_object()
        try:
            master_vm = VM.objects.get(vm_ip=cluster.master_ip)
        except VM.DoesNotExist:
            return JsonResponse({'error': 'Master VM not found'}, status=404)

        # 将 Cluster 和 VM 信息整合为简化的数据
        simplified_data = {
            'cluster_name': cluster.cluster_name,
            'master_ip': cluster.master_ip,
            'node_ips': cluster.node_ip,
            'vm_cpu' : master_vm.vm_cpu,
            'vm_memory' : master_vm.vm_memory,
            'vm_disk' : master_vm.vm_disk,

            # 添加其他你需要的字段
        }

        # 返回简化后的数据为 JSON 响应
        return JsonResponse(simplified_data, **response_kwargs)