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


class CreateVMsForm(forms.Form):
    kvm_name = forms.CharField(required=True, label='宿主机名')
    vm_name = forms.CharField(required=True, label='主机名')
    vcpus = forms.CharField(required=True, label='CPU 核数')
    memory = forms.CharField(required=True, label='内存大小')
    additional_disk = forms.CharField(required=True, label='额外磁盘大小')
    start_ip = forms.CharField(required=True, label='起始 IP')
    end_ip = forms.CharField(required=True, label='结束 IP')
class DeleteVMForm(forms.Form):
    kvm_name = forms.CharField(required=True, label='宿主机名')
    vm_name = forms.CharField(required=True, label='主机名')
class DeleteClusterNodeForm(forms.Form):
    cluster_name = forms.CharField(required=True, label='宿主机名')
    delete_node_ip = forms.CharField(required=True, label='节点 IP')
class DeleteClusterNodeForm(forms.Form):
    cluster_name = forms.CharField(label='Cluster Name')
    # delete_node_ip= forms.CharField(label='Delete Node IP', widget=forms.TextInput())
    delete_node_ip = forms.CharField(widget=forms.Textarea, required=True, label='要删除的节点 IP (用逗号分隔)')

    # 重写 __init__ 以接收多个 delete_node_ip
    # def __init__(self, *args, **kwargs):
    #     super(DeleteClusterNodeForm, self).__init__(*args, **kwargs)

    # def clean_delete_node_ip(self):
    #     # 将输入的多个 IP 地址作为列表返回，假设输入是以逗号分隔的字符串
    #     delete_node_ip = self.data.getlist('delete_node_ip')  # 确保你用 getlist 获取数组
    #     if not delete_node_ip:
    #         raise forms.ValidationError("至少要输入一个节点 IP")
    #     return delete_node_ip  # 现在 delete_node_ip 是个列表
class DeleteClusterForm(forms.Form):
    cluster_name = forms.CharField(required=True, label='集群名')
class CreateCluster_from_nodeForm(forms.Form):
    cluster_name = forms.CharField(required=True, label='集群名')
    master_ip = forms.CharField(required=True, label='主节点 IP')
    node_ip = forms.CharField(widget=forms.Textarea, required=True, label='节点 IP (用逗号分隔)')
    ntp_server = forms.CharField(required=False, label='NTP 服务器')