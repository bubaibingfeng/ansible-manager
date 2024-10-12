#!/usr/bin/env python
#coding: utf8
"Celery 异步操作Ansible 服务端"

import os, sys
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
        except: pass


if __name__ == "__main__":
    appCelery.worker_main()