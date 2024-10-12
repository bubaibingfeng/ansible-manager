## 软件需求

Deployment environment must have Ansible 2.4.0+
Master and nodes must have passwordless SSH access

## ansible 环境配置
```bash
#克隆仓库

ansible 代码仓库
git clone https://coding-prod.hengtiansoft.com/IMS-Libs/k3s-clusters-mgt.git

集群信息仓库
cd k3s-clusters-mgt
git clone https://coding-prod.hengtiansoft.com/IMS-Projects/ht-k3s-clusters.git
ln -sf ht-k3s-clusters/inventory/ inventory

拷贝镜像文件
#公司现在有存储服务吗，目前临时放在172.23.2.13:/root/k3s-clusters-mgt/roles/download/files
mkdir roles/download/files -p
scp root@172.23.2.13:/root/k3s-clusters-mgt/roles/download/files/*    roles/download/files/

```


## 初始化集群（创建）

1、在inventory/sample 基础上创建新项目的目录

```bash
cd k3s-clusters-mgt
cp -R inventory/example inventory/my-cluster
```

2、修改master，node的信息ip,账号密码
编辑 inventory/my-cluster/hosts.ini 文件

```bash
#初始master节点，必填，只能填一个。
[master-init]
m1 ansible_host=172.20.15.28 hostname=master1 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123
#ansible_host 主机ip
#hostname 主机名称
#ansible_ssh_user 用户名称
#ansible_ssh_pass 用户密码
#ansible_sudo_pass sudo密码

#选填。其他master节点,多master时，其他master节点放在这边。
[master]
m2 ansible_host=172.20.15.29 hostname=master2 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123
m3 ansible_host=172.20.15.33 hostname=master3 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123

#node节点。选填。所有node节点放这边。
[node]
n21ansible_host=172.20.15.34 hostname=node1 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123

[k3s_cluster:children]
master-init
master
node
```
3、配置group_vars
编辑 inventory/my-cluster/group_vars/all.yaml
```yaml
---
k3s_version: v1.22.3+k3s1  #k3s版本，一般不需要修改，如需修改，替换对应k3s的二进制文件
ansible_user: htuser  ###可能需要修改。ansible启动用户名称，一般为node节点的普通用户名。
systemd_dir: /etc/systemd/system #一般不需要修改
master_ip: "{{ hostvars[groups['master-init'][0]]['ansible_host'] | default(groups['master-init'][0]) }}"
#不需要修改
#argocd 访问地址 
argocd_endpoint: "https://172.24.100.41:32514"
argocd_user: "admin"
argocd_passwd: "PhqblaaCfgykOVEV"
  #新建集群在arogcd中的名称
argocd_cluster_name: "demo-k3s"

#一般不需要修改
dns_servers: ['172.30.5.10', '8.8.8.8']
extra_server_args: "--cluster-init"
extra_server_args: "--cluster-init --etcd-snapshot-dir=/tmp/db"
extra_agent_args: ""

#看情况修改
#k3s备份目录
k3s_backup_dir: "/tmp/k3s-backup"
#k3s恢复token和快照位置
k3s_restore_token_file: "/tmp/k3s-backup/token"
k3s_snapshot_restore_file: "/tmp/k3s-backup/on-demand-k3s-demo-m1-1690959357"
```

4、执行ansible脚本

```bash
ansible-playbook  -i inventory/my-cluster/hosts.ini create-k3s-cluster.yaml
```


## 添加node或者master
1、编辑 inventory/test inventory/my-cluster/hosts.ini 文件添加mater或者node信息，保证新加的master或者node没有k3s或者k3s-node服务。

```bash
#初始master节点
[master-init]
m1 ansible_host=172.20.15.28 hostname=master1 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123

#其他master节点
[master]
m2 ansible_host=172.20.15.29 hostname=master2 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123
m3 ansible_host=172.20.15.33 hostname=master3 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123
m3 ansible_host=172.20.15.30 hostname=master4 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123

#node节点
[node]
n21ansible_host=172.20.15.34 hostname=node1 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123
n21ansible_host=172.20.15.35 hostname=node2 ansible_ssh_user=htuser ansible_ssh_pass=HTuser123 ansible_sudo_pass=HTuser123

[k3s_cluster:children]
master-init
master
node
```

2、执行ansible脚本
```bash
ansible-playbook  -i inventory/my-cluster/hosts.ini create-k3s-cluster.yaml
```
##
## 删除节点
1、编辑reset.yml 文件,hosts：后为需要reset节点的ip或主机组，示例为node组。
```bash
---

- hosts: node
  gather_facts: yes
  become: yes
  roles:
    - role: reset
```
2、master节点中执行
```bash
#node1为节点名称
kubectl delete node node1

```
## 备份恢复集群
### 备份
1、编辑inventory/my-cluster/group_vars/all.yml文件,修改k3s_backup_dir目录的值。最好为远程存储挂载的目录
```bash
---
k3s_version: v1.22.3+k3s1
ansible_user: htuser
systemd_dir: /etc/systemd/system
master_ip: "{{ hostvars[groups['master-init'][0]]['ansible_host'] | default(groups['master-init'][0]) }}"
dns_servers: ['172.30.5.10', '8.8.8.8']
extra_server_args: "--cluster-init"
extra_server_args: "--cluster-init --etcd-snapshot-dir=/tmp/db"
extra_agent_args: ""
k3s_backup_dir: "/tmp/k3s-backup"
k3s_restore_token_file: "/tmp/k3s-backup/token"
k3s_snapshot_restore_file: "/tmp/k3s-backup/on-demand-master1-1685523512"
```
2、执行
```bash
ansible-playbook -i inventory/cc2/hosts.ini backup.yml
```


### 恢复
1、编辑inventory/my-cluster/group_vars/all.yml文件,修改k3s_restore_token_file，k3s_snapshot_restore_file的值，分别对应指定集群token和etcd的snapshot
```bash
---
k3s_version: v1.22.3+k3s1
ansible_user: htuser
systemd_dir: /etc/systemd/system
master_ip: "{{ hostvars[groups['master-init'][0]]['ansible_host'] | default(groups['master-init'][0]) }}"
dns_servers: ['172.30.5.10', '8.8.8.8']
extra_server_args: "--cluster-init"
extra_server_args: "--cluster-init --etcd-snapshot-dir=/tmp/db"
extra_agent_args: ""
k3s_backup_dir: "/tmp/k3s-backup"
k3s_restore_token_file: "/tmp/k3s-backup/token"
k3s_snapshot_restore_file: "/tmp/k3s-backup/on-demand-master1-1685523512"
```
2、执行
```bash
ansible-playbook -i inventory/cc2/hosts.ini restore.yml
```
##
## Kubeconfig

4、获取kubeconfig

```bash
ssh userlocal@master_ip "cat  ~/.kube/config"
```
