#ansible-manager

#### 介绍
ansible-manager 是基于Django + Ansible + Celery 的Web平台，用以批量ansible-playbook任务异步处理，可以用来开发给公司的运维部门，帮助
运维人员实现自动创建虚拟机、自动创建k3s集群等功能



#### 软件架构

软件架构说明
*   使用Ansible的playbook模式来自动化执行复杂的任务，在该系统已经实现的功能有:结合Terraform和kvm在远程宿主机上快速创建新的虚拟机，再通过创建k3s集群的脚本来快
*   搭建一个k3s集群,当然，也可以再编写新的playbook文件来实现新的功能。
*   Django负责处理路由和视图函数。
*   改写封装将ansibleapi函数，增加回写入数据库的插件后，将ansibleapi注册为celery的一个方法，这使得任务可以被异步处理，前端页面可以立即拿到
*    提交结果返回给用户，而不用等较长时间的ansible任务完全执行完毕，异步处理是必须的。



#### 安装教程

*   在程序中，默认Ansible使用ssh密码进行登录操作，也可改为使用私钥，私钥文件位置：`files/id_rsa`，或者在ansible.cfg中修改

*   手动部署
    *   安装 Python 环境，推荐Python 3.10.2，依赖环境根据python版本分为3.8.10和3.10.2两个版本，依赖文件有划分
    *   安装相关pagkage `pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
    *   配置相关参数 tools/config.py，包括redis、mysql，Ansible/settings.py 文件可修改 DATABASES 使用sqlite3
    *   为数据库建表，`python3 manage.py makemigrations && python3 manage.py migrate`
    *   在代码目录下启动Celery，`celery -A myCelery worker -l info`，可参看myCelery.py文件尾注释部分
    *   启动主服务，`python3 manage.py runserver 0.0.0.0:8000`。
*   服务启动
    * 启动celery，请设置 `export PYTHONOPTIMIZE=1`, 否则celery将无法调用ansible
    * Celery启动，`celery multi start 1 -A myCelery -l info -c4 --pidfile=tmp/celery_%n.pid -f logs/celery.log`
    * 主程序启动，`uwsgi --socket 127.0.0.1:9801 --module ansible_ui.wsgi --py-autoreload=1 --daemonize=logs/uwsgi.log`


#### 配置项

tools/config.py
在django的setting中指定mysql数据库参数，
在tools/config中指定redis参数

#### 使用说明

需外部提供MySQL和Redis，参数在tools/config.py内修改
常用命令放于1文本文档中
