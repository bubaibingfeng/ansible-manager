#!/usr/bin/env python
#coding: utf8
"Celery 异步操作Ansible 服务端"

import os, sys ,re
if os.environ.get("PYTHONOPTIMIZE", ""):
    print("开始启动")
else:
    print("\33[31m环境变量问题，Celery Client启动后无法正常执行Ansible任务，\n请设置export PYTHONOPTIMIZE=1；\n\33[32mDjango环境请忽略\33[0m")

import json
import time
from celery import Celery
from ansibleApi import *
from tools.config import BACKEND, BROKER, REDIS_ADDR, REDIS_PORT, REDIS_PD, ansible_result_redis_db
from celery.app.task import Task
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from public.templatetags.format import celery_status, ansible_result
celery_logger = get_task_logger(__name__)

appCelery = Celery("tasks",broker=BROKER,backend=BACKEND,)
sources = "scripts/inventory"

class MyTask(Task): # 回调
    def on_success(self, retval, task_id, args, kwargs):
        print("执行成功 notice from on_success")
        return super(MyTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        r = redis.Redis(host=REDIS_ADDR, password=REDIS_PD, port=REDIS_PORT, db=ansible_result_redis_db)
        a = redis.Redis(host=REDIS_ADDR, password=REDIS_PD, port=REDIS_PORT, db=4)
        tid = args[0]
        rlist = r.lrange(tid, 0, -1)
        try:
            at = AnsibleTasks.objects.filter(AnsibleID=tid)[0]
            at.AnsibleResult = json.dumps([ json.loads(i.decode()) for i in rlist ])
            ct = a.get('celery-task-meta-%s' % at.CeleryID).decode()
            at.CeleryResult = ct
            at.save()
        except: pass
        return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)



@appCelery.task(bind=True,base=MyTask)  #
def ansiblePlayBook(self, tid, playbooks, extra_vars, **kw):
    psources = kw.get('sources') or extra_vars.get('sources') or sources
    AnsiblePlaybookExecApi29(task_id=tid, playbook_path=playbooks, inventory_file=psources, extra_vars=extra_vars)
    return 'success'


import os
import sys
import django
path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,path)
os.environ['DJANGO_SETTINGS_MODULE']='ansible_ui.settings'
django.setup()
from public.models import *

@appCelery.task(bind=True)
def syncAnsibleResult(self, ret, *a, **kw):     # 执行结束，结果保持至db
    c = AsyncResult(self.request.get('parent_id'))
    celery_logger.info(c.result)
    tid = kw.get('tid', None)
    if tid:
        r = redis.Redis(host=REDIS_ADDR, password=REDIS_PD, port=REDIS_PORT, db=ansible_result_redis_db)
        a = redis.Redis(host=REDIS_ADDR, password=REDIS_PD, port=REDIS_PORT, db=4)
        rlist = r.lrange(tid, 0, -1)
        try:
         at = AnsibleTasks.objects.filter(AnsibleID=tid)[0]
         at.AnsibleResult = json.dumps([ json.loads(i.decode()) for i in rlist ])
         ct = a.get('celery-task-meta-%s' % at.CeleryID).decode()
         at.CeleryResult = ct
         at.save()
         print("同步结果至db: syncAnsibleResult !!!!!: parent_id: %s" % self.request.get('parent_id'), a, kw)
         return 'success'
        except Exception as e:
        # 捕获异常并返回错误信息
         celery_logger.error(f"Error in syncAnsibleResult: {str(e)}")
         return {'status': 'error', 'message': str(e)}
def parse_ansible_result(ansible_result):
    # 定义用于匹配 CPU、Memory、Disk 使用率的正则表达式
    status_pattern = r"CPU Usage:\s*(\d+\.\d+)%.*Memory Usage:\s*(\d+\.\d+)%.*Disk Usage:\s*(\d+)%"
    # 使用正则表达式匹配 AnsibleResult 中的 VM 状态
    match = re.search(status_pattern, ansible_result)
    
    if match:
        # 提取 CPU, Memory 和 Disk 使用率
        cpu_usage = float(match.group(1))
        memory_usage = float(match.group(2))
        disk_usage = int(match.group(3))
        
        # 构建 JSON 格式的数据
        result_data = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage
        }
        
        # 返回 JSON 数据
        return json.dumps(result_data)
    
    else:
        # 如果没有匹配到数据，返回空的 JSON
        return json.dumps({"error": "No state found in the result"})
from django.core.serializers import serialize
from django.utils import timezone
@appCelery.task(bind=True)
# def write_kvm_state(self,pk,vm_name,*a, **kw):
def write_kvm_state(ret,pk, vm_name):
        print(f"PK: {pk}")
        print(f"VM Name: {vm_name}")
        time.sleep(7)
        ansibletasks=AnsibleTasks.objects.get(pk=pk)
        ansible_result_text = ansible_result(ansibletasks.AnsibleResult)
        print(f"ansible_result_text: {ansible_result_text}")
        json_result = parse_ansible_result(ansible_result_text)
        print(f"json_result: {json_result}")
        # data = json.loads(serialize('json', [vm]))[0]
        parsed_json = json.loads(json_result)
        memory_usage = parsed_json.get('memory_usage', None)
        disk_usage = parsed_json.get('disk_usage', None)
        cpu_usage = parsed_json.get('cpu_usage', None)
        current_time = datetime.datetime.now()
        print(current_time)
        State.objects.update_or_create(
                    vm_name=vm_name,
                    defaults={'vm_cpu_usage':cpu_usage,'vm_memory_usage': memory_usage, 'vm_disk_usage': disk_usage, 'update_time': current_time}
                )
@appCelery.task(bind=True)
def write_kvm_create(ret,pk, kvm_name):
        print(f"PK: {pk}")
        print(f"VM Name: {vm_name}")
        time.sleep(100)
        ansibletasks=AnsibleTasks.objects.get(pk=pk)
        ansible_result_text = ansible_result(ansibletasks.AnsibleResult)
        print(f"ansible_result_text: {ansible_result_text}")
        json_result = parse_ansible_result(ansible_result_text)
        print(f"json_result: {json_result}")
        # data = json.loads(serialize('json', [vm]))[0]
        parsed_json = json.loads(json_result)
        print(parsed_json)
        print(current_time)
        # State.objects.update_or_create(
        #             vm_name=vm_name,
        #             defaults={'vm_cpu_usage':cpu_usage,'vm_memory_usage': memory_usage, 'vm_disk_usage': disk_usage, 'update_time': current_time}
        #         )
        KVM.objects.filter(kvm_name=kvm_name).delete()


if __name__ == "__main__":
    appCelery.worker_main()