# inventory.tf的变量文件

variable "cluster_name" {
  description = "name of the cluster"
  type        = string
}

variable "master_ips" {
  description = "A list of IP addresses for the master nodes"
  type        = list(string)
}

variable "node_ips" {
  description = "A list of IP addresses for the worker nodes"
  type        = list(string)
}

variable "master_hostnames" {
  description = "A list of hostnames for the master nodes"
  type        = list(string)
}

variable "node_hostnames" {
  description = "A list of hostnames for the worker nodes"
  type        = list(string)
}