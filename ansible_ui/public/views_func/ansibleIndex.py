from django.shortcuts import render
from django.views.generic import DetailView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
import json, datetime, redis, os, random, string, ast,re,time
from myCelery import ansiblePlayBook, syncAnsibleResult,write_kvm_state
from tools.config import REDIS_ADDR, REDIS_PORT, REDIS_PD, ansible_result_redis_db
from public.models import *
from public.admin import writeini,find_available_ip
from public.forms import *
from django.shortcuts import get_object_or_404
from django.core.serializers import serialize
from public.views import update_vm_ip_reachability
def remove_ssh_host_key(hostname):
    import subprocess
    import os
    try:
        # 使用ssh-keygen的安全方式删除特定主机记录
        subprocess.run(
            ['ssh-keygen', '-R', hostname],
            check=True,
            capture_output=True
        )
        print(f"成功删除主机 {hostname}的记录")
    except subprocess.CalledProcessError as e:
        print(f"删除失败: {e}")
    except FileNotFoundError:
        print("未找到ssh-keygen命令")
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
        update_vm_ip_reachability()
        vms = VM.objects.filter(vm_useable=True, vm_ip_reachable=True)
        Clusters = Cluster.objects.all()
        form = CreateCluster_from_nodeForm() 
        return render(request, 'ansible/create_cluster_from_node.html', {'clusters':Clusters,'vms': vms, 'form': form})
    def post(self, request):
        print(request.POST)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        form = CreateCluster_from_nodeForm(data)
        if form.is_valid():
            try:
                cluster_name = form.cleaned_data['cluster_name']
                master_ip = form.cleaned_data['master_ip']
                node_ips = form.cleaned_data['node_ip'].split(',')
                ntp_server = form.cleaned_data['ntp_server']
                # 写入 INI 文件
                writeini(master_ip=master_ip, node_ip=node_ips)
                # {'domain':'47.109.199.70','etcd_url':' http://47.109.199.70:2379'}
                extra_vars_dict = {}
                extra_vars_dict["argocd_cluster_name"] =cluster_name
                if ntp_server !="":
                    ntp_server = form.cleaned_data['ntp_server']
                    extra_vars_dict["ntp_server"] = ntp_server
                else:
                    ntp_server = "172.30.5.10"
                    extra_vars_dict["ntp_server"] = ntp_server
                # extra_vars_dict["domain"] = '47.109.199.70'
                # extra_vars_dict["etcd_url"] = 'http://47.109.199.70:2379'
                # 执行 Ansible playbook
                TaskUser = request.user
                playbook2 = ['playbooks/create-k3s-cluster.yaml']
                data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook2, user=TaskUser, extra_vars=extra_vars_dict)
                # 更新或创建集群
                Cluster.objects.update_or_create(
                    cluster_name=cluster_name,
                    master_ip=master_ip,
                    defaults={'node_ip': node_ips,'ntp_server': ntp_server}
                )
                vms_to_update = VM.objects.filter(vm_ip__in=node_ips)
                vms_to_update.update(vm_useable=False)
                vms_to_update = VM.objects.filter(vm_ip=master_ip)
                vms_to_update.update(vm_useable=False)

       
       
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


# class CreateHostsView(LoginRequiredMixin, View):
#     def get(self, request):
#         form = CreateHostsForm()
#         return render(request, 'ansible/create_hosts.html', {'form': form})

#     def post(self, request):
#         data = json.loads(request.body)
#             # 使用表单验证数据
#         form = CreateHostsForm(data)
#         if form.is_valid():
#             try:
#                 vm_name = form.cleaned_data['vm_name']
#                 vm_ip = form.cleaned_data['vm_ip']
#                 vm_ssh_user = form.cleaned_data['vm_ssh_user']
#                 vm_ssh_pass = form.cleaned_data['vm_ssh_pass']
#                 vm_ssh_port = form.cleaned_data['vm_ssh_port']
                
#                 kvm, created = KVM.objects.update_or_create(
#                     vm_name=vm_name,
#                     defaults={'vm_ip': vm_ip, 'vm_ssh_user': vm_ssh_user, 'vm_ssh_pass': vm_ssh_pass, 'vm_ssh_port': vm_ssh_port}
#                 )
                
#                 writeini()
                
#                 status_code = 201 if created else 200
#                 return JsonResponse({
#                     'message': 'Host created successfully' if created else 'Host updated successfully',
#                     'vm_name': vm_name
#                 }, status=status_code)
#             except Exception as e:
#                 return JsonResponse({'error': str(e)}, status=500)
#         else:
#             return JsonResponse({'errors': form.errors}, status=400)




class DeleteHostView(LoginRequiredMixin, View):
    def get(self, request):
        form = DeleteHostForm()
        return render(request, 'ansible/', {'form': form})
    def post(self, request):

        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
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
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            # 使用表单验证数据
        form = CreateVMsForm(data)
        # form = CreateVMsForm(request.POST)
        if form.is_valid():
            try:
                kvm_name = form.cleaned_data['kvm_name']
                vm_name = form.cleaned_data['vm_name']
                if VM.objects.filter(vm_name=vm_name).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': f'虚拟机名称 "{vm_name}" 已被占用'
                    })
                vcpus = form.cleaned_data['vcpus']
                memory = form.cleaned_data['memory']    
                additional_disk = form.cleaned_data['additional_disk']
                start_ip = form.cleaned_data['start_ip']
                end_ip = form.cleaned_data['end_ip']
                vm_ssh_user = "userlocal"
                vm_ssh_pass = "HTuser123"
                vm_ssh_port = "22"
                vm_ip=find_available_ip(start_ip,end_ip)
                remove_ssh_host_key(vm_ip)
                # kvm_instance = KVM.objects.get(vm_name=kvm_name)
                # kvm_password = kvm_instance.vm_ssh_pass
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
                # extra_vars_dict["kvm_password"] = kvm_password
                TaskUser = request.user
                playbook = ['playbooks/create_vm.yml']
                data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook, user=TaskUser, extra_vars=extra_vars_dict)
                print(data)
                vm, created = VM.objects.update_or_create(
                    vm_name=vm_name,
                    defaults={'kvm_name':kvm_name,'vm_ip': vm_ip, 'vm_cpu': vcpus, 'vm_memory': memory, 'vm_disk': additional_disk, 'vm_ssh_user': vm_ssh_user, 'vm_ssh_pass': vm_ssh_pass, 'vm_ssh_port': vm_ssh_port}
                )
                State.objects.update_or_create(
                    vm_name=vm_name,
                )
                writeini()
                status_code = 201 if created else 200
                return JsonResponse({
                    'message': 'VM created successfully' if created else 'VM updated successfully',
                    'vm_name': vm_name,
                    'vm_ip': vm_ip
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
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
            # 使用表单验证数据
        form = DeleteVMForm(data)
        # form = DeleteVMForm(request.POST)
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
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            # 使用表单验证数据
        form = CreateHostsForm(data)
        # form = CreateHostsForm(request.POST)
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
                remove_ssh_host_key(vm_ip)
                writeini()
                TaskUser = self.request.user
                playbook = ['playbooks/ensure_file.yml']
                extra_vars_dict = {}
                extra_vars_dict["kvm_name"] = vm_name
                extra_vars_dict["kvm_password"] = vm_ssh_pass
                tid = "AnsibleApiPlaybook-%s-%s" % (''.join(random.sample(string.ascii_letters + string.digits, 2)),
                        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
                at = AnsibleTasks(
                                AnsibleID=tid,
                                TaskUser=TaskUser,
                                GroupName=None,
                                ExtraVars=extra_vars_dict,
                                playbook=playbook,
                            )
                at.save()
                pk=at.pk
                print(pk)
                celeryTask = ansiblePlayBook.apply_async(
                        (tid, playbook, extra_vars_dict),
                        link=[
                            syncAnsibleResult.s(tid=tid),
                            # write_kvm_state.si(pk=pk,vm_name=vm_name)
                        ]
                    )
                at=AnsibleTasks.objects.get(AnsibleID=tid)
                at.CeleryID=celeryTask.id
                at.save()
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
        vm_name=VM.objects.all()
        
        return render(request, 'ansible/delete_hosts.html', {'form': form, 'vm_name': vm_name})
    def post(self, request):
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST  
            # 使用表单验证数据
        form = CreateVMsForm(data)
        # form = DeleteHostForm(request.POST)
        if form.is_valid():
            try:
                vm_name = form.cleaned_data['vm_name']
                vm = get_object_or_404(KVM, vm_name=vm_name)
                if vm.vm_name == vm_name:
                    vm_name = vm.vm_name  # 保存名称以用于响应消息
                    vm.delete()
                    writeini()
                else:
                    return JsonResponse({
                        'error': 'Invalid credentials. Deletion failed.'
                    }, status=403)
                return JsonResponse({
                    'message': 'Host deleted successfully',
                    'vm_name': vm_name
                }, status=200)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return
class DeleteNodeView(LoginRequiredMixin, View):
    def get(self, request):
        cluster = Cluster.objects.all()
        form = DeleteClusterNodeForm()
        return render(request, 'ansible/delete_node.html', {'form': form, 'cluster': cluster})
    def post(self, request):
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        form = DeleteClusterNodeForm(data)
        if form.is_valid():
            try:
                cluster_name = form.cleaned_data['cluster_name']
                # delete_node_ip = clean_delete_node_ip('delete_node_ip', [])  # 确保这个字段在表单中定义
                delete_node_ips = form.cleaned_data['delete_node_ip'].split(',')
                cluster = get_object_or_404(Cluster, cluster_name=cluster_name)
                master_ip =cluster.master_ip
                # 校验 master_ip 和要删除的节点 IP
                for delete_node_ip in delete_node_ips:
                    if delete_node_ip in cluster.node_ip:
                        vm=VM.objects.get(vm_ip=delete_node_ip)
                        vm.vm_useable=True
                        if isinstance(cluster.node_ip, str):
                            cluster.node_ip = json.loads(cluster.node_ip)
                        cluster.node_ip.remove(delete_node_ip)
                        # 写入 INI 文件
                    else:
                        return JsonResponse({
                            'error': '要删除的节点不在集群中。删除失败。'
                        }, status=403)
                cluster.save()
                vm.save()

                writeini(master_ip, delete_node_ips)
                playbook1 = ['playbooks/reset.yml']
                playbook2 = ['playbooks/delete_node.yml']
                TaskUser = request.user
                extra_vars = {'groupname': delete_node_ips}  # 使用 delete_node_ip
                        # 调用 Ansible 执行 playbook
                AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook1, user=TaskUser, extra_vars=extra_vars)
                AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook2, user=TaskUser, extra_vars=extra_vars)
                return JsonResponse({
                            'message': '这些节点已成功删除',
                            'cluster_name': cluster_name,
                            'delete_node_ip': delete_node_ip,
                        }, status=200)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
class ClusteraddnodeView(LoginRequiredMixin, View):
    def get(self, request):
        update_vm_ip_reachability()
        cluster = Cluster.objects.all()
        vms = VM.objects.filter(vm_useable=True, vm_ip_reachable=True)
        form = CreateCluster_from_nodeForm()
        return render(request, 'ansible/cluster_add_node.html', {'vms': vms, 'form': form,'cluster': cluster})
    def post(self, request):
        print(request.POST)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        form = CreateCluster_from_nodeForm(data)
        if form.is_valid():
            try:
                cluster_name = form.cleaned_data['cluster_name']
                master_ip = form.cleaned_data['master_ip']
                node_ips = form.cleaned_data['node_ip'].split(',')
                ntp_server = form.cleaned_data['ntp_server']
                # 更新或创建集群
                cluster = get_object_or_404(Cluster, cluster_name=cluster_name, master_ip=master_ip)
                extra_vars_dict = {}
                if ntp_server !="":
                    extra_vars_dict["ntp_server"] = ntp_server
                else:
                    ntp_server = "172.30.5.10"
                    extra_vars_dict["ntp_server"] = ntp_server
                # 获取现有的 node_ip 列表
                existing_node_ips = cluster.node_ip

                # 确保现有的 node_ip 是一个列表
                if not isinstance(existing_node_ips, list):
                    existing_node_ips = []
                # 将新的 node_ips 追加到现有的列表中
                existing_node_ips.extend(node_ips)
                # 去除重复的 IP（可选）
                existing_node_ips = list(set(existing_node_ips))
                # 写入 INI 文件
                writeini(master_ip=master_ip, node_ip=existing_node_ips)
                # {'domain':'47.109.199.70','etcd_url':' http://47.109.199.70:2379'}
                extra_vars_dict["argocd_cluster_name"] =cluster_name
                # extra_vars_dict["domain"] = master_ip
                # extra_vars_dict["etcd_url"] = f"http://{master_ip}:2379"
                # extra_vars_dict["domain"] = '47.109.199.70'
                # extra_vars_dict["etcd_url"] = 'http://47.109.199.70:2379'

                # 执行 Ansible playbook
                TaskUser = request.user
                playbook2 = ['playbooks/create-k3s-cluster.yaml']
                data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook2, user=TaskUser, extra_vars=extra_vars_dict)
                # 更新并保存
                cluster.node_ip = existing_node_ips
                cluster.save()

                vms_to_update = VM.objects.filter(vm_ip__in=node_ips)
                vms_to_update.update(vm_useable=False)

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
class DeleteClusterView(LoginRequiredMixin, View):
    def get(self, request):
        form = DeleteClusterForm()
        cluster=Cluster.objects.all()
        return render(request, 'ansible/delete_cluster.html', {'form': form, 'cluster': cluster})
    def post(self, request):
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            # 使用表单验证数据
        form = DeleteClusterForm(data)
        # form = DeleteClusterForm(request.POST)
        if form.is_valid():
            try:
                cluster_name = form.cleaned_data['cluster_name']
                cluster = get_object_or_404(Cluster, cluster_name=cluster_name)
                master_ip = cluster.master_ip
                node_ips = cluster.node_ip
                node_ips.append(master_ip)
                for node_ip in node_ips:
                    vm = VM.objects.get(vm_ip=node_ip)
                    kvm=KVM.objects.get(vm_name=vm.kvm_name)
                    extra_vars_dict = {}
                    extra_vars_dict["kvm_name"] = kvm.vm_name
                    extra_vars_dict["kvm_password"] =kvm.vm_ssh_pass
                    extra_vars_dict["vm_name"] = vm.vm_name
                    TaskUser = request.user
                    playbook = ['playbooks/delete_vm.yml']
                    data = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook, user=TaskUser, extra_vars=extra_vars_dict)
                    vm.delete()
                cluster.delete()
                return JsonResponse({
                    'message': 'these ips deleted successfully',
                    'vm_ip': node_ips
                }, status=200)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
from public.templatetags.format import ansible_result
from celery import chain
class KVMStateView(LoginRequiredMixin,DetailView):
    model = KVM
    slug_field = 'vm_name'
    slug_url_kwarg = 'vm_name'
    def render_to_response(self, context, **response_kwargs):
        vm_name = self.kwargs.get('vm_name')
        vm = get_object_or_404(KVM, vm_name=vm_name)
        data = json.loads(serialize('json', [vm]))[0]
        TaskUser = self.request.user
        playbook = ['playbooks/get_state.yml']
        extra_vars_dict = {}
        extra_vars_dict["groupname"] = vm_name
        # data2 = AnsibleOpt.ansible_playbook(groupName=None, playbook=playbook, user=TaskUser, extra_vars=extra_vars_dict)
        tid = "AnsibleApiPlaybook-%s-%s" % (''.join(random.sample(string.ascii_letters + string.digits, 2)),
                datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        at = AnsibleTasks(
                        AnsibleID=tid,
                        TaskUser=TaskUser,
                        GroupName=None,
                        ExtraVars=extra_vars_dict,
                        playbook=playbook,
                     )
        at.save()
        pk=at.pk
        print(pk)
        celeryTask = ansiblePlayBook.apply_async(
                (tid, playbook, extra_vars_dict),
                link=[
                    syncAnsibleResult.s(tid=tid),
                    write_kvm_state.si(pk=pk,vm_name=vm_name)
                ]
            )
        # celeryTask = chain(
        #         ansiblePlayBook.s(tid, playbook, extra_vars_dict),
        #         syncAnsibleResult.s(tid=tid),
        #         write_kvm_state.si(pk=pk, vm_name=vm_name)
        #     )    
        at=AnsibleTasks.objects.get(AnsibleID=tid)
        current_time = datetime.datetime.now()
        print(current_time)
        at.CeleryID=celeryTask.id
        at.save()
        # ansibletasks=AnsibleTasks.objects.get(pk=data2['pk'])
        # ansible_result_text = ansible_result(ansibletasks.AnsibleResult)
        # json_result = parse_ansible_result(ansible_result_text)
        # data = json.loads(serialize('json', [vm]))[0]
        # parsed_json = json.loads(json_result)
        # memory_usage = parsed_json.get('memory_usage')
        # disk_usage = parsed_json.get('disk_usage')
        # cpu_usage = parsed_json.get('cpu_usage')
        # current_time = datetime.datetime.now()
        # State.objects.update_or_create(
        #             vm_name=vm_name,
        #             defaults={'vm_cpu_usage':cpu_usage,'vm_memory_usage': memory_usage, 'vm_disk_usage': disk_usage, 'update_time': current_time}
        #         )
        try:
            state = State.objects.get(vm_name=vm_name)
            state=json.loads(serialize('json', [state]))[0]
            simplified_data = {
                'vm_name': data['fields']['vm_name'],
                'vm_ip': data['fields']['vm_ip'],
                'vm_cpu_usage':state['fields']['vm_cpu_usage'],
                'vm_memory_usage':state['fields']['vm_memory_usage'],
                'vm_disk_usage':state['fields']['vm_disk_usage'],
                'update_time':state['fields']['update_time'],
            }
            return JsonResponse(simplified_data)
        except State.DoesNotExist:
            # 如果没有找到对象，返回自定义的 JSON 响应
            return JsonResponse({
                'status': 'pending',
                'message': '数据正在更新中,请等待10s后重新刷新'
            })
class VMStateView(LoginRequiredMixin,DetailView):
    model = VM
    slug_field = 'vm_name'
    slug_url_kwarg = 'vm_name'
    def render_to_response(self, context, **response_kwargs):
        vm_name = self.kwargs.get('vm_name')
        vm = get_object_or_404(VM, vm_name=vm_name)
        data = json.loads(serialize('json', [vm]))[0]
        TaskUser = self.request.user
        playbook = ['playbooks/get_state.yml']
        extra_vars_dict = {}
        extra_vars_dict["groupname"] = vm_name
        tid = "AnsibleApiPlaybook-%s-%s" % (''.join(random.sample(string.ascii_letters + string.digits, 2)),
                datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        at = AnsibleTasks(
                        AnsibleID=tid,
                        TaskUser=TaskUser,
                        GroupName=None,
                        ExtraVars=extra_vars_dict,
                        playbook=playbook,
                     )
        at.save()
        pk=at.pk
        print(pk)
        celeryTask = ansiblePlayBook.apply_async(
                (tid, playbook, extra_vars_dict),
                link=[
                    syncAnsibleResult.s(tid=tid),
                    write_kvm_state.si(pk=pk,vm_name=vm_name)
                ]
            )
        at=AnsibleTasks.objects.get(AnsibleID=tid)
        current_time = datetime.datetime.now()
        print(current_time)
        at.CeleryID=celeryTask.id
        at.save()
        try:
            state = State.objects.get(vm_name=vm_name)
            state=json.loads(serialize('json', [state]))[0]
            simplified_data = {
                'vm_name': data['fields']['vm_name'],
                'vm_ip': data['fields']['vm_ip'],
                'vm_cpu_usage':state['fields']['vm_cpu_usage'],
                'vm_memory_usage':state['fields']['vm_memory_usage'],
                'vm_disk_usage':state['fields']['vm_disk_usage'],
                'update_time':state['fields']['update_time'],
            }
            return JsonResponse(simplified_data)
        except State.DoesNotExist:
            # 如果没有找到对象，返回自定义的 JSON 响应
            return JsonResponse({
                'status': 'pending',
                'message': '数据正在更新中,请等待10s后重新刷新'
            })