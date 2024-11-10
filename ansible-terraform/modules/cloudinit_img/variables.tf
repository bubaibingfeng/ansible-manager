# modules/cloudinit_img/variables.tf

# cloudinit_img的文件名
variable "name" {
  type = string 
}

# cloudinit.cfg文件传入路径
variable "base_file" {
  type = string
  default = "/path/to/cloudinit.cfg"  
}