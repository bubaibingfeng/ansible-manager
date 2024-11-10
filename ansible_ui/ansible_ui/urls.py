# url 配置入口 ansible_ui/urls.py，内容可直接覆盖

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from public.views_func.account import myLogin, myLogout
from public.views_func.kvm import *
from public.views_func.ansibleIndex import *
from public.views import *
urlpatterns = [
    # 所有 admin 开头的请求，交给 admin.site.urls 处理，django 自带系统，无需修改
    path('admin/', admin.site.urls),
    # 我们将所有以 /ansible/ 开头的 uri 交给 public.urls 处理，对应了 public/urls.py 文件
    path('ansible/', include('public.urls'),),
    # 添加登陆相关映射
    path('account/login', myLogin),
    path('account/logout', myLogout),
    path('', RedirectView.as_view(url='/ansible/')),
    path('hosts/add',CreateHostsView.as_view()),
    path('hosts/list',KVMList.as_view()),
    path('hosts/list2',KVMList2.as_view()),
    path('hosts/info/<str:vm_name>',KVMDetailView.as_view()),
    path('hosts/state/<str:vm_name>',KVMStateView.as_view()),
    # path('hosts/<int:pk>/', AnsibleTaskDetail.as_view()),
    path('hosts/delete',DeleteHostView.as_view()),
    path('VM/add',CreateVMsView.as_view()),
    path('VM/delete',DeleteVMsView.as_view()),
    path('VM/list',VMList.as_view()),
    path('VM/info/<str:vm_name>',VMDetailView.as_view()),
    path('VM/state/<str:vm_name>',VMStateView.as_view()),
    path('cluster/add_from_node/', CreateClusterView.as_view()),
    path('cluster/list/',ClusterList.as_view()),
    path('cluster/info/<str:cluster_name>',ClusterDetailView.as_view()),
    path('cluster/delete_node/',DeleteNodeView.as_view()),
    path('cluster/add_node/',ClusteraddnodeView.as_view()),
    path('cluster/delete',DeleteClusterView.as_view()),
    path('cluster/state/<str:cluster_name>',ClusterStateDetailView.as_view()),
    # path('VM/state/update/all,')
    # path('VM')
]