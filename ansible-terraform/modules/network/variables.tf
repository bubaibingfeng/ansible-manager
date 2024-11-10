# 网络的variables
variable "name" {
  description = "The name of the network"
  type        = string
}

variable "judgement" {
  description = "Whether to create the network or not"
  type        = bool
  default     = false  # 默认不创建网络，可以根据需要更改此值
}


