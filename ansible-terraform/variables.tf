# 变量声明

# 虚拟机名称的变量
variable "vm_name" {
  type    = list(string)
  default = ["test-vm1", "test-vm2", "test-vm3"]
}
# 虚拟机额外磁盘的变量
variable "additional_size" {
  description = "Additional disk size in GB"
  type        = number
}

# 虚拟机的网络的变量
variable "network_name" {
  type = string
  description = "network name"
}

# 虚拟机的内存的变量
variable "memory" {
  type = number
  description = "memory by mb"
}

# 虚拟机的vcpu数量的变量
variable "vcpus" {
  type = number
  description = "number of vcpus"
}

# 虚拟机的数量的变量
variable "vm_number" {
  type = number
  description = "number of virtual machines"
}

# 虚拟机的镜像的变量
variable "base_image" {
  type = string
  description = "镜像位置"
}

# 虚拟机写入的SSH公钥
variable "ssh_public_keys" {
  type = list(string)

  default = [
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC2yKZCgWJKD4Dl9g3+/Ec10SjqvWQUY4uzrXxbtfds9oYQ+Zb2UVjS3vmNAGZTAzwlSe0jOzwLegixH/abHMI85uwbCqsD2V+n2xsgMhEOEKFvTm1E9o/Pj6y99VaYgNowmGtjw3tIYeMgc5NmxqIXVL/9cNfalFPGb6Y1JIvx4NO5W3lIk2z53xue3r28GKcYtf+pJOSjk+9tiiGRfLiypbKI8zLREWtpY77waJ9ISeyRqPoGMZR3IYtCu2Sxm7Qbdih2kEF9pQmUYfIcB1XyI6v3D2mPxaYOikHU4KQqm6BESFlel3LvuREquut7TzFTSEODGr8rBX7zhRmwgTkujFKRtjgbtu7ETNhKcI95tOiysGDmHHTYFqkDPATOrtwQWT9rKOxX8A8+SRb9qsdfpXC+t9QfuPHsg/5n85qrGZv/sorXxBCK4ZKL2lexBI/4F5kSR5THwxEbESGXSo14mflF2VTCqvKAZ3udEA72uYfMklvdN9q3YwLCyAMY1Ys= root@frank-server",
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDXv6N+7sRBlujJo9V4KMdTZv2T8er42aIgvOIcXf29+qnm5C3Xx5sgD8Ri4/681GoPBomAPjlfWmNgwuYHlxn5wkT8AuWxqpcFiUSu/CEkOEuWJ34vCNpl5nQ4qmXys51Zsx1mnbNgAu0kojCmz+m2BKtJIKux8O1UhiGIsymL7gQmU2p6AGt9PuMU7tG6mJvagKL0zKqB07jigBafA1QyUgmGmWEy8D6BFRe0mYdUAS2RNf5XILQoRYNRlxYgM3kX9gZB9HvSDQMf8yaiBAT6NryuYAY8RKXzwiN6+mRst0lcHDI9P2yJAyMXiKMPoQkYWT/SiozawTewWLZqVEezhuRV3jLpThAShm09WOXVEPgRo9Do0R1gLHvDzeoJeK0YLtHrdBs6AlLvj5IZNtSrBxUfZ0g4MDoe3Y7eI86fKHuNLZFydbI7Kqwp9VqsaSeEsW1QsvQ8b+lil9JkAJQfb8Tk+fank1IUOVbTyrk9iiXEP1R9/oCx3N5ZDFBrcek= limol@Franklin-Laptop"
  ]
  description = "ssh public key"
}


# 虚拟机名称的变量
variable "username" {
  type    = string
  default = "userlocal"
}

# 虚拟机的密码的变量
variable "password" {
  description = "Enter the sha512password for the VM"
  type = string 
}

# 静态IP组变量
variable "static_ip" {
  type = list(string)
  default     = ["192.168.1.3","192.168.1.4"]
  description = "静态IP"
}

# 子网掩码变量
variable "subnet_mask" {
  type = number
  default     = "24" 
  description = "子网掩码"
}

# 网关变量
variable "gateway_ip" {
  type = string
  default     = "172.20.134.254" 
  description = "网关地址"
}

# DNS服务器变量
variable "dns_servers" {
  type = list(string)
  default = [
    "172.30.5.10",
    "114.114.114.114"
  ]
  description = "DNS地址"
}

# inventory主机名
variable "master_hostnames" {
  description = "A list of hostnames for the master nodes"
  type        = list(string)
}

variable "node_hostnames" {
  description = "A list of hostnames for the worker nodes"
  type        = list(string)
}

# inventory对应ip
variable "masters_ips" {
  description = "A list of IP addresses for the master nodes"
  type        = list(string)
}

variable "nodes_ips" {
  description = "A list of IP addresses for the worker nodes"
  type        = list(string)
}

# k3s集群名称
variable "cluster_name" {
  description = "K3S cluster name"
  type        = string
}

variable "network_judgement" {
  description = "Whether to create the network or not"
  type        = bool
  default     = false  # 默认不创建网络，可以根据需要更改此值
}
