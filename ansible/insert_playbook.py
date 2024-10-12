import os
import sys
import django
path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,path)
os.environ['DJANGO_SETTINGS_MODULE']='ansible_ui.settings'
django.setup()

from public.models import *
from django.contrib.auth.models import User

pb,b = AnsiblePlaybooks.objects.get_or_create(playbook='test_debug.yml')
if b:
    print('创建测试 playbook')
    pb.nickName = '测试Debug'
    pb.playbook = 'test_debug.yml'
    pb.save()
else:
    print('测试 playbook 已存在')