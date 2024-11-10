# module的绝对路径
locals {
  module_path = path.module
}

# 通过传入的cloudinit.cfg文件创建cloudinit.img文件
resource "local_file" "cloudinit_img" {
  filename = "${local.module_path}/${var.name}.img" # 临时路径，可以根据实际情况更改
  content  = "" 

    provisioner "local-exec" {
      command = <<EOT
        cloud-localds  ${local_file.cloudinit_img.filename} ${var.base_file}
      EOT
    }
}

# 输出cloudinit.img的路径
output "cloudinit_img_path" {
  value = local_file.cloudinit_img.filename
}

