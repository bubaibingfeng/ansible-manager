# create_config的变量文件

# 文件名变量
variable "filename" {
  type = string
  description = "cloudinit filename"
}

# 主机名变量
variable "hostname" {
  type = string
  description = "hostname"
}

# 用户名变量
variable "username" {
  type = string
  description = "user name"
}

# sha512加密的密码变量
variable "sha512password" {
  type = string
  default = ""
  description = "userpassword in sha512 format"
}

# ssh_keys变量（public key）
variable "ssh_keys" {
  type = list(string)

  default = [
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC2yKZCgWJKD4Dl9g3+/Ec10SjqvWQUY4uzrXxbtfds9oYQ+Zb2UVjS3vmNAGZTAzwlSe0jOzwLegixH/abHMI85uwbCqsD2V+n2xsgMhEOEKFvTm1E9o/Pj6y99VaYgNowmGtjw3tIYeMgc5NmxqIXVL/9cNfalFPGb6Y1JIvx4NO5W3lIk2z53xue3r28GKcYtf+pJOSjk+9tiiGRfLiypbKI8zLREWtpY77waJ9ISeyRqPoGMZR3IYtCu2Sxm7Qbdih2kEF9pQmUYfIcB1XyI6v3D2mPxaYOikHU4KQqm6BESFlel3LvuREquut7TzFTSEODGr8rBX7zhRmwgTkujFKRtjgbtu7ETNhKcI95tOiysGDmHHTYFqkDPATOrtwQWT9rKOxX8A8+SRb9qsdfpXC+t9QfuPHsg/5n85qrGZv/sorXxBCK4ZKL2lexBI/4F5kSR5THwxEbESGXSo14mflF2VTCqvKAZ3udEA72uYfMklvdN9q3YwLCyAMY1Ys= root@frank-server",
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDXv6N+7sRBlujJo9V4KMdTZv2T8er42aIgvOIcXf29+qnm5C3Xx5sgD8Ri4/681GoPBomAPjlfWmNgwuYHlxn5wkT8AuWxqpcFiUSu/CEkOEuWJ34vCNpl5nQ4qmXys51Zsx1mnbNgAu0kojCmz+m2BKtJIKux8O1UhiGIsymL7gQmU2p6AGt9PuMU7tG6mJvagKL0zKqB07jigBafA1QyUgmGmWEy8D6BFRe0mYdUAS2RNf5XILQoRYNRlxYgM3kX9gZB9HvSDQMf8yaiBAT6NryuYAY8RKXzwiN6+mRst0lcHDI9P2yJAyMXiKMPoQkYWT/SiozawTewWLZqVEezhuRV3jLpThAShm09WOXVEPgRo9Do0R1gLHvDzeoJeK0YLtHrdBs6AlLvj5IZNtSrBxUfZ0g4MDoe3Y7eI86fKHuNLZFydbI7Kqwp9VqsaSeEsW1QsvQ8b+lil9JkAJQfb8Tk+fank1IUOVbTyrk9iiXEP1R9/oCx3N5ZDFBrcek= limol@Franklin-Laptop"
  ]
  description = "ssh public key"
}

# timezone变量
variable "timezone" {
  type        = string
  default     = "Asia/Shanghai" 
  description = "The timezone for the instance"
}

# packages变量
variable "packages" {
  type = list(string)
  default = [
    "vim",
    "net-tools",
    "curl"
  ]
  description = "packages to install"
}

# 静态IP变量
variable "static_ip" {
  type = string
  default     = "192.168.1.3" 
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
