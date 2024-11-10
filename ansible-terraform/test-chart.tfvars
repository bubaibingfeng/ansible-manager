# variables.tfvars 声明的变量的值

# 虚拟机名称
vm_name = ["test-chart-1", "test-chart-2"]

# 集群个节点名称
master_hostnames = [ "test-chart-1" ]
node_hostnames = [ "test-chart-2" ]

# 集群名称
cluster_name = "test-chart"

# 用户名
username = "userlocal"

# 密码
password = "$6$KywVZaUlE8YmzEoK$XYQ0b/tGjZJXK0KVwQshmnXQMu8NBeMwB/5CMbneKGw601YmdWsTemY0AQqEypwj7FhxPahv3o6J1vtMWNPZo/"

# 虚拟机数量
vm_number = 3

# 虚拟机使用镜像
base_image = "/home/userlocal/cloud-img/jammy-server-cloudimg-amd64.img"

# 虚拟机内存（单位mb）
memory = 8192

# 虚拟机CPU数量
vcpus = 4

# 虚拟机加入的网络名称
network_name = "test_nat"

# ssh公钥
ssh_public_keys = [ 
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCYj3FpEhgXHvh6KaZSkRLGI/eXxKKtYJJav6v230GisjVFRaeEeDo46NdDygLNJPSVRFYKF35b+HJhIZ+g/MxKuvmgB3nC8Pfde21elPgk3hdhjy7yH0Q9rJ8clZQO1XjnpU4Hnwca9/NnZvmTC1Ou4PRTcfRgNkgVI6Q7F8IcAmdxKypsu18yKXdfUpjoxNqScZwxbYDjJ36eSDAxwTQDzVD+ukAKuxCzStay+oBCnsbj4jCbz1gPTnJPqvHOxfNKjPvKeiwzsjx0fw823LJPRsmU2UcNo9CJiA+9pP9bJpBJ2Ne0i0qWhN+XdmMAUiMobRq4K4SY2+IpWrOdbm75ukFVbwrXOn5hJqrog2puPHxBksopiolHzJkK6ksX2der/frh4pZTeI1Sbm2CeLvYAYqELLG1urs4mE0R0LisOeyWwMtCPbKU8SoYhPKjjEfm2WKIB/en4yRO0fACSYnnk6lYgIUk5/nAOBsh3ZPL73ag4cTNlbVn7fALq5zOl9M= root@test-oom",
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAW1/zrmHe6pnozA4jR4xMSVOAjA7CDVIdpodHdnr1PD caojianfeng@outlook.com",
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCoFEIKy2i6d38wIOyoSUVG2lVf74vdmJ5zQRw6TnOqonkjnV3+uU5iEI+LhEemEsHTa9nXPKI26uhjTDtqtt5QucMEtGQT6AIQ+JMrwJBGmL5I3UzQSqMW3P/If3QkhgnqCYiF2sz+RRnvA+lD5zlkSYS9mrKKc9ug9ggRXgbjVuFhQDwjPej9stYOc2exla7waReTlCN3Q1rr27Mq9JxGwsE1CN+sYZ7QVPJTG9WlsLwAJzdfR+yZ+voKfEcUb9jKXCfShVWY8tM4f2RyDE6tcafIT5YdauFs6OG1dM00/LV9F5BPQfdv1TBmiVDyGpTuRU7MlL7TgJbGLWY8AUqtOHbBeMoZR+bAJZRMi0uPHGhGlJ1WtV6NuCBE20/l7KgK4o+av+xM2G0BdGridAjR/Rw6FvgTVzpH6j61lfkQlmnA3MREiKiC1gBt9I7lQwkNgRbDxBlfnrS7KjqTBR/pZTYQallpgjsPvo+cXHLlpSYGDmXSskQwqB1TN+940l8= limol@Frank-ThinkPad",
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCgj+lwu7nQkNsPwoulYKgcbkZ8PzYP04OJNnKnWL/hQODzrfVU5iGQAV7J4XBgIP+m12tzoTqFb6bBfudWj3FIZQItcWMo4lucyEnlULbmmojodCA/lDKqEPqfglNyw1rhj1CYrbVvcM28oF/DXAtEz79NOEpWqLbU0flJmNqeAVu5/RCCMisiiNlnCHsFWBQeuVfyaRi8WHNt3X+5pw08hVg7gF9iup8Pnw72MN7yPOv9U0RWuYeVuXsl41ucfahc9Dgtq+JOTHySGDNvJhuDE9tLwNfMeek2NhdNOEWysGIuJaQsBYBjCDNd0qyALi2QPsrarrd8A8mz0tni/Lt0qBKxRA8oQCpP/kOrFIiw+Q9Se6JAXcOTAhRrkVwc8VxlhcjcPWBMZ11pRFdiIvwsb0W/pgplhvTSmLFwbqMinIg2UWJ25mNFawWh+FaoxkAsZ+WAXIrCenr8aS+cQUSpXRsvFPPMWhuMjppyzdXhCeX7EgqsQFmrbesqhC1C1Z0= root@cicd-kvm-node1"
    ]

# 静态IP组变量
static_ip = [
    "172.20.134.42",
    "172.20.134.43"
]

# 集群IP对应
masters_ips = [
    "172.20.134.42"
]

nodes_ips = [
    "172.20.134.43"
]


# 子网掩码变量
subnet_mask = 24


# 网关变量
gateway_ip = "172.20.134.254"


# DNS服务器变量
dns_servers  = [
    "172.30.5.10",
    "114.114.114.114"
]
