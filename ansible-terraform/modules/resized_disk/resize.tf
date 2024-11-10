# 复制并增加硬盘空间
resource "null_resource" "copy_and_resize_image" {
  provisioner "local-exec" {
    command = <<EOT
      cp ${var.base_image_path} ${var.new_image_path}
      qemu-img resize ${var.new_image_path} +${var.additional_size}G
    EOT
  }

  triggers = {
    base_image_path   = var.base_image_path
    new_image_path    = var.new_image_path
    additional_size   = var.additional_size
  }
}

# 输出新img的文件路径
output "resized_image_path" {
  value = var.new_image_path
}
