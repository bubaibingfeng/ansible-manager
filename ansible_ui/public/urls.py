from django.urls import path
from public.views import AnsibleTaskList, AnsibleTaskDetail, index   # 导入我们的 views 方法
from public.views_func.ansibleIndex import *
from public.views_func.kvm import *

# 这里定义的使用请求路径都已经加了前缀 /ansible/
urlpatterns = [
    # 指定 uri 路径的请求交给特定 views 方法处理，
    # 指定 /ansible/ansible_task_list/ 请求交给 AnsibleTaskList  处理
    path('get_Ansible_Tasks/', AnsibleTaskList.as_view()),
    # 指定detail 映射，其中 pk 会传递给 AnsibleTaskDetail 处理
    path('get_Ansible_Tasks_Detail/<int:pk>/', AnsibleTaskDetail.as_view()),
    path('push_playbook/', PlaybookView.as_view()), # playbook 处理页面
    path('', index),    # 指定 /ansible/ 请求交给 index 处理
    path('get_groups/', AnsibleGroupsList.as_view()),
    path('get_cluster/', AnsibleClustersList.as_view()),
    path('delete_node/', DeleteNodeView.as_view()), # playbook 处理页面
    # path("cluster/add_from_node",)
]