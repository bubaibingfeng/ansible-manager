# resize.tf的变量

# base_image_path: 原镜像的路径
variable "base_image_path" {
  type = string
}

# new_image_path: 新镜像的路径
variable "new_image_path" {
  type = string
}

# additional_size: 扩容的大小 默认增加10G
variable "additional_size" {
  type = number
  default = 10 # 默认扩容10G
}

