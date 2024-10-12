from django import forms

class CreateClusterForm(forms.Form):
    master_ip = forms.CharField(required=True, label='主节点 IP')
    node_ips = forms.CharField(widget=forms.Textarea, required=True, label='节点 IP (用逗号分隔)')


class CreateHostsForm(forms.Form):
    vm_ip = forms.CharField(required=True, label='主机 IP')
    vm_name = forms.CharField(required=True, label='主机名')
    vm_ssh_user = forms.CharField(required=True, label='SSH 用户')
    vm_ssh_pass = forms.CharField(required=True, label='SSH 密码')
    vm_ssh_port = forms.CharField(required=True, label='SSH 端口')



class DeleteHostForm(forms.Form):
    vm_name = forms.CharField(required=True, label='主机名')
    vm_ssh_pass = forms.CharField(required=True, label='SSH 密码')


class CreateVMsForm(forms.Form):
    kvm_name = forms.CharField(required=True, label='宿主机名')
    vm_name = forms.CharField(required=True, label='主机名')
    vcpus = forms.CharField(required=True, label='CPU 核数')
    memory = forms.CharField(required=True, label='内存大小')
    additional_disk = forms.CharField(required=True, label='额外磁盘大小')

class DeleteVMForm(forms.Form):
    kvm_name = forms.CharField(required=True, label='宿主机名')
    vm_name = forms.CharField(required=True, label='主机名')


class CreateCluster_from_nodeForm(forms.Form):
    cluster_name = forms.CharField(required=True, label='集群名')
    master_ip = forms.CharField(required=True, label='主节点 IP')
    node_ips = forms.CharField(widget=forms.Textarea, required=True, label='节点 IP (用逗号分隔)')
