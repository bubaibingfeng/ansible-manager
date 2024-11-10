# 验证虚拟机存活的模块变量

variable "vm_ips" {
  description = "List of VM IP addresses to check"
  type        = list(string)
}
