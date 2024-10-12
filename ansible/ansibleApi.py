


import json
import shutil
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.inventory.host import Host
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C
from ansible.utils.ssh_functions import check_for_controlpersist
from ansible.executor.playbook_executor import PlaybookExecutor
import logging, logging.handlers
import datetime
try:
    from rich import print
except:
    pass
from collections import namedtuple
from collections import defaultdict
import redis

# redis callback 写入 db
from tools.config import REDIS_ADDR, REDIS_PORT,REDIS_PD, ansible_remote_user, ansible_result_redis_db


Options = namedtuple('Options', [
    'listtags', 'listtasks', 'listhosts', 'syntax', 'connection',
    'module_path', 'forks', 'remote_user', 'private_key_file', 'timeout',
    'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
    'scp_extra_args', 'become', 'become_method', 'become_user',
    'verbosity', 'check', 'extra_vars', 'playbook_path', 'passwords',
    'diff', 'gathering', 'remote_tmp',
])


def get_default_options():
    options = dict(
        syntax=False,
        timeout=30,
        connection='ssh',
        forks=10,
        remote_user='root',
        private_key_file='files/id_rsa',
        become=None,
        become_method=None,
        become_user=None,
        verbosity=1,
        check=False,
        diff=False,
        start_at_task=None,
        gathering='implicit',
        remote_tmp='/tmp/.ansible'
    )
    return options
class BaseHost(Host):
    def __init__(self, host_data):
        self.host_data = host_data
        hostname = host_data.get('hostname') or host_data.get('ip')
        port = host_data.get('port') or 22
        super().__init__(hostname, port)
        self.__set_required_variables()
        self.__set_extra_variables()

    def __set_required_variables(self):
        print('BaseHost.__set_required_variables')
        host_data = self.host_data
        self.set_variable('ansible_host', host_data['ip'])
        self.set_variable('ansible_port', host_data.get('port', 22))

        if host_data.get('username'):
            self.set_variable('ansible_user', host_data['username'])

        if host_data.get('private_key'):
            self.set_variable('ansible_ssh_private_key_file', host_data['private_key'])
        if host_data.get('password'):
            self.set_variable('ansible_ssh_pass', host_data['password'])

        become = host_data.get("become", False)
        if become:
            self.set_variable("ansible_become", True)
            self.set_variable("ansible_become_method", become.get('method', 'sudo'))
            self.set_variable("ansible_become_user", become.get('user', 'root'))
            self.set_variable("ansible_become_pass", become.get('pass', ''))
        else:
            self.set_variable("ansible_become", False)

    def __set_extra_variables(self):
        for k, v in self.host_data.get('vars', {}).items():
            self.set_variable(k, v)

    def __repr__(self):
        return self.name
# 处理主机与组关系
class BaseInventory(InventoryManager):
    loader_class = DataLoader
    variable_manager_class = VariableManager
    host_manager_class = BaseHost

    def __init__(self, host_list=[], group_list=[],):
        print('BaseInventory: host_list - %s; group_list = %s' % (host_list, group_list))
        self.host_list = host_list
        self.group_list = group_list
        self.loader = self.loader_class()
        self.variable_manager = self.variable_manager_class()
        super().__init__(self.loader)

    def get_groups(self):
        return self._inventory.groups

    def get_group(self, name):
        return self._inventory.groups.get(name, None)

    def get_or_create_group(self, name):
        group = self.get_group(name)
        if not group:
            self.add_group(name)
            return self.get_or_create_group(name)
        else:
            return group

    def parse_groups(self):
        for g in self.group_list:
            parent = self.get_or_create_group(g.get("name"))
            children = [self.get_or_create_group(n) for n in g.get('children', [])]
            for child in children:
                parent.add_child_group(child)

    def parse_hosts(self):
        group_all = self.get_or_create_group('all')
        ungrouped = self.get_or_create_group('ungrouped')
        for host_data in self.host_list:
            print('host_data： %s' % host_data)
            host = self.host_manager_class(host_data=host_data)
            self.hosts[host_data.get('hostname') or host_data.get('ip')] = host
            groups_data = host_data.get('groups')
            if groups_data:
                for group_name in groups_data:
                    group = self.get_or_create_group(group_name)
                    group.add_host(host)
            else:
                ungrouped.add_host(host)
            group_all.add_host(host)

    def parse_sources(self, cache=False):
        self.parse_groups()
        self.parse_hosts()

    def get_matched_hosts(self, pattern):
        return self.get_hosts(pattern)


class AnsibleError(Exception):
    pass


class RedisCallBack(CallbackBase):
    "Ansible Api 和 Ansible Playbook V2 api 调用该CallBack"
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'redis3'
    CALLBACK_TYPE = 'stdout'
    def __init__(self, id):     # 初始化时要求传入任务 id
        super(RedisCallBack, self).__init__()
        self.id = id
        self.r = redis.Redis(host=REDIS_ADDR, port=REDIS_PORT, password=REDIS_PD, db=ansible_result_redis_db)

    def _write_to_save(self, data):  # 写入 redis
        msg = json.dumps(data, ensure_ascii=False)
        self.r.rpush(self.id, msg)
        # 为了方便查看，我们 print 写入 redis 的字符串的前 50 个字符
        print("\33[34m写入Redis：%.50s......\33[0m" % msg)

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = u"PLAY"
        else:
            msg = u"PLAY [%s]" % name
        print(msg)

    def v2_runner_on_ok(self, result, **kwargs):
        "处理成功任务，跳过 setup 模块的结果"
        host = result._host
        if "ansible_facts" in result._result.keys():    # 我们忽略 setup 操作的结果
            print("\33[32mSetUp 操作，不Save结果\33[0m")
        # else:
        #     self._write_to_save({
        #         "host": host.name,
        #         "result": result._result,
        #         "task": result.task_name,
        #         "status": "success"
        #     })
    def v2_runner_on_failed(self, result, ignore_errors=False, **kwargs):
        "处理执行失败的任务，有些任务失败会被忽略，所有有两种状态"
        host = result._host
        if ignore_errors:
            status = "ignoring"
        else:
            status = 'failed'
        self._write_to_save({
                "host": host.name,
                "result": result._result,
                "task": result.task_name,
                "status": "failed"
            })
    def v2_runner_on_skipped(self, result, *args, **kwargs):
        "处理跳过的任务"
        # self._write_to_save({
        #         "host": host.name,
        #         "result": result._result,
        #         "task": result.task_name,
        #         "status": "success"
        #     })
    def v2_runner_on_unreachable(self, result, **kwargs):
        "处理主机不可达的任务"
        host = result._host
        self._write_to_save({
                "host": host.name,
                "result": result._result,
                "task": result.task_name,
                "status": "success"
            })

    def v2_playbook_on_notify(self, handler, host):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_start(self, playbook):
        pass


class PlayBookTaskQueueManager_V2(TaskQueueManager):

    def __init__(self, inventory, variable_manager, loader, passwords, stdout_callback=None, run_additional_callbacks=True, run_tree=False):
        super().__init__(inventory, variable_manager, loader, passwords, stdout_callback, run_additional_callbacks, run_tree)

        self.forks = context.CLIARGS.get('forks')
        self._stdout_callback = stdout_callback

    def load_callbacks(self):   # 为callback 设置存储id
        pass


# 重新封装 PlaybookExecutor ， 传入 task_id
class MyPlaybookExecutor_V2(PlaybookExecutor):

    def __init__(self, task_id, playbooks, inventory, variable_manager, loader, passwords):
        self._playbooks = playbooks
        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self.passwords = passwords
        self._unreachable_hosts = dict()

        if context.CLIARGS.get('listhosts') or context.CLIARGS.get('listtasks') or \
                context.CLIARGS.get('listtags') or context.CLIARGS.get('syntax'):
            self._tqm = None
        else:
            self._tqm = PlayBookTaskQueueManager_V2(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords=self.passwords,
                stdout_callback=RedisCallBack(task_id)
            )
        check_for_controlpersist(C.ANSIBLE_SSH_EXECUTABLE)


class MyTaskQueueManager(TaskQueueManager):
    # def load_callbacks(self):   # 截断callback，只保留自定义
        pass


# 执行 ansible 模块任务
def AnsibleExecApi29(task_id, tasks=[], inventory_data=None):
    options = get_default_options()
    context.CLIARGS = ImmutableDict(options)

    loader = DataLoader()
    passwords = dict(vault_pass='secret')
    results_callback = RedisCallBack(task_id)
    # inventory = InventoryManager(loader=loader, sources='localhost,')
    inventory = BaseInventory(inventory_data)
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    play_source = dict(
            name="Ansible Play",
            hosts='localhost',
            gather_facts='no',
            tasks=tasks,
        )
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
    tqm = None
    try:
        tqm = MyTaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords=passwords,
                stdout_callback=results_callback,
            )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()

        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)


# Ansible 2.9 版本的 vars/manager.py: VariableManager 未有 extra_vars.setter
class VariableManagerVars(VariableManager):

    @property
    def extra_vars(self):
        return self._extra_vars

    @extra_vars.setter
    def extra_vars(self, value):
        self._extra_vars = value.copy()


# 执行 Ansible Playbook
def AnsiblePlaybookExecApi29(task_id, playbook_path, inventory_data=None, extra_vars={}, inventory_file=None):
    # playbook_path = ['playbooks/test_debug.yml']
    print(task_id, playbook_path, inventory_data, extra_vars, inventory_file)
    print('playbook_path is')
    print(playbook_path)
    print(type(playbook_path))
    print('inventory_data is')
    print(inventory_file)
    passwords = ""
    options = get_default_options()
    loader = DataLoader()

    # 如果输入主机与组对应关系，调用自定义关系模块，否则，调用 inventory 文件
    # if inventory_data:
    #     inventory = BaseInventory(inventory_data)
    # else:
    inventory = InventoryManager(loader=loader, sources=inventory_file)
    variable_manager = VariableManagerVars(loader=loader, inventory=inventory)
    variable_manager.extra_vars = extra_vars
    executor = MyPlaybookExecutor_V2(
        task_id=task_id,
        playbooks=playbook_path,
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={"conn_pass": passwords},
    )

    context.CLIARGS = ImmutableDict(options)
    executor.run()


if __name__ == '__main__':
    # task_id = "AnsibleExec_%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    # tasks = [
    #     dict(action=dict(module='shell', args='ls'), register='shell_out'),
    #     dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
    # ]
    # AnsibleExecApi29(task_id, tasks)
    playbook_path='debug.yml'
    AnsiblePlaybookExecApi29(
        task_id='AnsiblePlaybook_%s' % datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        playbook_path=['ansible_ui/playbooks/debug.yml'],
        extra_vars={'content': '1'},
        inventory_file='scripts/inventory',
    )