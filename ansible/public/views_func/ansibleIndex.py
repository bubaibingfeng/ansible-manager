from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
import json, datetime, redis, os, random, string, ast
from myCelery import ansiblePlayBook, syncAnsibleResult
from tools.config import REDIS_ADDR, REDIS_PORT, REDIS_PD, ansible_result_redis_db
from public.models import *
from public.admin import writeini,find_available_ip
from public.forms import *
from django.shortcuts import get_object_or_404

class AnsibleOpt:
    @staticmethod
    def ansible_playbook(groupName, playbook, user=None, extra_vars={}, **kw):
        tid = "AnsibleApiPlaybook-%s-%s" % (''.join(random.sample(string.ascii_letters + string.digits, 2)),
                datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        # if not extra_vars.get('groupName'):
        #      extra_vars['groupName'] = groupName
        celeryTask = ansiblePlayBook.apply_async(
                (tid, playbook, extra_vars),
                link=syncAnsibleResult.s(tid=tid)
            ) # 保存 ansible 结果
        at = AnsibleTasks(
                        AnsibleID=tid,
                        CeleryID=celeryTask.task_id,
                        TaskUser=user,
                        GroupName=groupName,
                        ExtraVars=extra_vars,
                        playbook=playbook,
                     )
        at.save()
        return {"playbook": playbook,
                "extra_vars": extra_vars,
                "ansible_id": tid,
                "celeryTask": celeryTask.task_id,
                "groupName": groupName,
                "pk":at.pk}
# playbook 编辑和处理页面
class PlaybookView(LoginRequiredMixin, View):
    def get(self, request):
        ansisble_playbooks = AnsiblePlaybooks.objects.all()
        groups=Groups.objects.all()
        return render(request, 'ansible/playbookIndex.html', {'ansisble_playbooks': ansisble_playbooks,'groups':groups})

    def post(self, request):
        print(request.POST)
        TaskUser = request.user
        groupName = request.POST.get('groupName', None)
        playbook = request.POST.get('playbook', None)
        playbook2=[playbook]
        extraVars = request.POST.get('extra_vars','')
        print(extraVars)
        extra_vars = ast.literal_eval(extraVars) if extraVars else {}
        if not playbook:
            return
        data = AnsibleOpt.ansible_playbook(groupName, playbook2, TaskUser, extra_vars)
        return redirect('/ansible/get_Ansible_Tasks_Detail/%s/' % data.get('pk'))

class CreateClusterView(LoginRequiredMixin, View):
    def get(self, request):
        vms = VM.objects.filter(vm_useable=True, vm_ip_reachable=True)
        form = CreateCluster_from_nodeForm() 
        return render(request, 'ansible/create_cluster_from_node.html', {'vms': vms, 'form': form})

    def post(self, request):
        print(request.POST)
        form = CreateCluster_from_nodeForm(request.POST)
        if form.is_valid():
            try:
                cluster_name = form.cleaned_data['cluster_name']
                master_ip = form.cleaned_data['master_ip']
                node_ips = form.cleaned_data['node_ips'].split(',')

                
                # 写入 INI 文件

                writeini(master_ip, node_ips)
                # {'domain':'47.109.199.70','etcd_url':' http://47.109.199.70:2379'}
                extra_vars_dict = {}
                # extra_vars_dict["domain"] = master_ip
                # extra_vars_dict["etcd_url"] = f"http://{master_ip}:2379"
                extra_vars_dict["domain"] = '47.109.199.70'
                extra_vars_dict["etcd_url"] = 'http://47.109.199.70:2379'

                # 执行 Ansible playbook
                TaskUser = request.user
                playbook2 = ['playbooks/create-k3s-cluster.yaml']
                data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook2, user=TaskUser, extra_vars=extra_vars_dict)

                # 更新或创建集群
                Cluster.objects.update_or_create(
                    cluster_name=cluster_name,
                    master_ip=master_ip,
                    defaults={'node_ip': node_ips}
                )

                return JsonResponse({
                        'message': 'Cluster created/updated successfully',
                        'cluster_name': cluster_name,
                        'master_ip': master_ip,
                        'node_ips': node_ips
                    }, status=200)
            except Exception as e:
            # 捕获其他可能的异常并返回错误信息
             return JsonResponse({'error': str(e)}, status=500)

        else:
                # 表单验证失败时，返回错误信息
                return JsonResponse({'errors': form.errors}, status=400)
        # update_or_create() 方法首先会尝试查找一个 master_ip 匹配的 Cluster 对象。
# 如果找到匹配的对象，它会使用 defaults 字典中的值更新该对象。在这个例子中，会更新 node_ip 字段。
# 如果没有找到匹配的对象，它会创建一个新的 Cluster 对象，使用 master_ip 参数和 defaults 字典中的值。
        # return HttpResponse("ok")
class AnsibleGroupsList(LoginRequiredMixin, View):
    def get(self, request):
        ansisble_groups = Groups.objects.all
        return render(request, 'ansible/groups_list.html', {'ansisble_groups': ansisble_groups})
class AnsibleClustersList(LoginRequiredMixin, View):
    def get(self, request):
        ansisble_clusters = Cluster.objects.all
        return render(request, 'ansible/clusters_list.html', {'ansisble_clusters': ansisble_clusters})
class DeleteNodeView(LoginRequiredMixin, View):
    def get(self, request):
        master_ip = Cluster.objects.all()
        # groups=Groups.objects.all()
        return render(request, 'ansible/delete_node.html', {'master_ip': master_ip})

    def post(self, request):
        print(request.POST)
        TaskUser = request.user

        # groupName = request.POST.get('groupName', None)
        # playbook = request.POST.get('playbook', None)
        playbook1=['playbooks/reset.yml']
        playbook2=['playbooks/delete_node.yml']
        extraVars = request.POST.get('extra_vars','')
        master_ip = request.POST.get('master_ip', None)
        nodeip = request.POST.getlist('node_ips[]', None)
        cluster_names = request.POST.get('cluster_name', None)
        newdata=Cluster.objects.get(master_ip=master_ip)
        writeini(master_ip,nodeip)
        newip = [ip.strip()[1:-1] for ip in newdata.node_ip[1:-1].split(',')]
#         我们首先去掉输入字符串的首尾方括号 input_str[1:-1]
# 然后用逗号分割字符串 .split(',')
# 对每个分割后的项使用 strip() 去除空白字符
# 最后用 [1:-1] 去掉每个IP地址周围的单引号
        for x in nodeip:
            newip.remove(x)
        print(newip)
        print(nodeip)
        newdata.node_ip=newip
        newdata.save()
        # Cluster.objects.create(cluster_name=cluster_names, master_ip=master_ip,node_ip=nodeip)
        print(extraVars)
        extra_vars = ast.literal_eval(extraVars) if extraVars else {'groupname':nodeip}
        # if not playbook:
        #     return
        # data = AnsibleOpt.ansible_playbook(groupName=None,playbook2, TaskUser, extra_vars)
        data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook1, user=TaskUser, extra_vars=extra_vars)
        data2 = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook2, user=TaskUser, extra_vars=extra_vars)
        return redirect('/ansible/get_Ansible_Tasks_Detail/%s/' % data.get('pk'))
        # return HttpResponse("ok") 

class CreateHostsView(LoginRequiredMixin, View):
    def get(self, request):
        form = CreateHostsForm()
        return render(request, 'ansible/create_hosts.html', {'form': form})

    def post(self, request):
        data = json.loads(request.body)
            
            # 使用表单验证数据
        form = CreateHostsForm(data)
        
        if form.is_valid():
            try:
                vm_name = form.cleaned_data['vm_name']
                vm_ip = form.cleaned_data['vm_ip']
                vm_ssh_user = form.cleaned_data['vm_ssh_user']
                vm_ssh_pass = form.cleaned_data['vm_ssh_pass']
                vm_ssh_port = form.cleaned_data['vm_ssh_port']
                
                kvm, created = KVM.objects.update_or_create(
                    vm_name=vm_name,
                    defaults={'vm_ip': vm_ip, 'vm_ssh_user': vm_ssh_user, 'vm_ssh_pass': vm_ssh_pass, 'vm_ssh_port': vm_ssh_port}
                )
                
                writeini()
                
                status_code = 201 if created else 200
                return JsonResponse({
                    'message': 'Host created successfully' if created else 'Host updated successfully',
                    'vm_name': vm_name
                }, status=status_code)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'errors': form.errors}, status=400)



class DeleteHostView(LoginRequiredMixin, View):
    def get(self, request):
        form = DeleteHostForm()
        return render(request, 'ansible/delete_hosts.html', {'form': form})
    def post(self, request):
        data = json.loads(request.body)
            
            # 使用表单验证数据
        form = DeleteHostForm(data)
        if form.is_valid():
            vm_name = form.cleaned_data['vm_name']
            vm_ssh_pass = form.cleaned_data['vm_ssh_pass']
            
            try:
                kvm = get_object_or_404(KVM, vm_name=vm_name)
                # 验证提供的信息是否匹配
                if kvm.vm_name == vm_name and kvm.vm_ssh_pass == vm_ssh_pass:
                    kvm_name = kvm.vm_name  # 保存名称以用于响应消息
                    kvm.delete()
                    # 假设writeini()函数需要在删除后更新某些配置
                    writeini()
                    return JsonResponse({
                        'message': f'Host {kvm_name} deleted successfully'
                    }, status=200)
                else:
                    return JsonResponse({
                        'error': 'Invalid credentials. Deletion failed.'
                    }, status=403)
            except Exception as e:
                return JsonResponse({
                    'error': str(e)
                }, status=500)
        else:
            return JsonResponse({
                'errors': form.errors
            }, status=400)


class CreateVMsView(LoginRequiredMixin, View):
    def get(self, request):
        form = CreateHostsForm()
        kvm_name=KVM.objects.all()
        return render(request, 'ansible/create_vm.html', {'form': form, 'kvm_name': kvm_name})

    def post(self, request):
        # data = json.loads(request.body)
            
        #     # 使用表单验证数据
        # form = CreateVMsForm(data)
        form = CreateVMsForm(request.POST)
        if form.is_valid():
            try:
                kvm_name = form.cleaned_data['kvm_name']
                vm_name = form.cleaned_data['vm_name']
                vcpus = form.cleaned_data['vcpus']
                memory = form.cleaned_data['memory']    
                additional_disk = form.cleaned_data['additional_disk']
                vm_ssh_user = "userlocal"
                vm_ssh_pass = "HTuser123"
                vm_ssh_port = "22"
                # 下面写入数据库的过程应该放在一个事务中，如果失败则回滚

                vm_ip=find_available_ip("172.20.134.45","172.20.134.200")
                kvm_instance = KVM.objects.get(vm_name=kvm_name)
                kvm_password = kvm_instance.vm_ssh_pass
                
                extra_vars_dict = {}
                extra_vars_dict["kvm_name"] = kvm_name
                extra_vars_dict["vm_name"] = json.dumps([vm_name])
                extra_vars_dict["var_name"] = vm_name
                extra_vars_dict["master_hostnames"] = json.dumps([vm_name])
                extra_vars_dict["static_ip"] = json.dumps([vm_ip])
                extra_vars_dict["masters_ips"] = json.dumps([vm_ip])
                extra_vars_dict["additional_disk"] = additional_disk
                extra_vars_dict["vcpus"] = vcpus
                extra_vars_dict["memory"] = memory
                extra_vars_dict["kvm_password"] = kvm_password

                TaskUser = request.user
                playbook = ['playbooks/create_vm.yml']
                data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook, user=TaskUser, extra_vars=extra_vars_dict)
                print(data)

                vm, created = VM.objects.update_or_create(
                    vm_name=vm_name,
                    defaults={'kvm_name':kvm_name,'vm_ip': vm_ip, 'vm_cpu': vcpus, 'vm_memory': memory, 'vm_disk': additional_disk, 'vm_ssh_user': vm_ssh_user, 'vm_ssh_pass': vm_ssh_pass, 'vm_ssh_port': vm_ssh_port}
                )
                
                writeini()
                
                status_code = 201 if created else 200
                return JsonResponse({
                    'message': 'VM created successfully' if created else 'VM updated successfully',
                    'vm_name': vm_name
                }, status=status_code)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'errors': form.errors}, status=400)


class DeleteVMsView(LoginRequiredMixin, View):
    def get(self, request):
        form = DeleteVMForm()
        vm_name=VM.objects.all()
        return render(request, 'ansible/delete_vm.html', {'form': form, 'vm_name': vm_name})
    def post(self, request):
        # data = json.loads(request.body)
            
        #     # 使用表单验证数据
        # form = CreateVMsForm(data)
        form = DeleteVMForm(request.POST)
        if form.is_valid():
            try:
                kvm_name = form.cleaned_data['kvm_name']
                vm_name = form.cleaned_data['vm_name']
                vm = get_object_or_404(VM, vm_name=vm_name)
                if vm.vm_name == vm_name and vm.kvm_name == kvm_name:
                    vm_name = vm.vm_name  # 保存名称以用于响应消息
                    vm.delete()
                    writeini()
                else:
                    return JsonResponse({
                        'error': 'Invalid credentials. Deletion failed.'
                    }, status=403)
                kvm_instance = KVM.objects.get(vm_name=kvm_name)
                kvm_password = kvm_instance.vm_ssh_pass
                # 下面写入数据库的过程应该放在一个事务中，如果失败则回滚
                extra_vars_dict = {}
                extra_vars_dict["kvm_name"] = kvm_name
                extra_vars_dict["kvm_password"] = kvm_password
                extra_vars_dict["vm_name"] = vm_name
                TaskUser = request.user
                playbook = ['playbooks/delete_vm.yml']
                data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook, user=TaskUser, extra_vars=extra_vars_dict)
                return JsonResponse({
                    'message': 'VM deleted successfully',
                    'vm_name': vm_name
                }, status=200)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'errors': form.errors}, status=400)



class CreateHostsView(LoginRequiredMixin, View):
    def get(self, request):
        form = CreateHostsForm()
        return render(request, 'ansible/create_hosts.html', {'form': form})

    def post(self, request):
        data = json.loads(request.body)
            
            # 使用表单验证数据
        form = CreateHostsForm(data)
        
        if form.is_valid():
            try:
                vm_name = form.cleaned_data['vm_name']
                vm_ip = form.cleaned_data['vm_ip']
                vm_ssh_user = form.cleaned_data['vm_ssh_user']
                vm_ssh_pass = form.cleaned_data['vm_ssh_pass']
                vm_ssh_port = form.cleaned_data['vm_ssh_port']
                
                kvm, created = KVM.objects.update_or_create(
                    vm_name=vm_name,
                    defaults={'vm_ip': vm_ip, 'vm_ssh_user': vm_ssh_user, 'vm_ssh_pass': vm_ssh_pass, 'vm_ssh_port': vm_ssh_port}
                )
                
                writeini()
                
                status_code = 201 if created else 200
                return JsonResponse({
                    'message': 'Host created successfully' if created else 'Host updated successfully',
                    'vm_name': vm_name
                }, status=status_code)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'errors': form.errors}, status=400)