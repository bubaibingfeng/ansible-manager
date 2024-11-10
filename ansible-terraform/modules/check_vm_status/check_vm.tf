resource "null_resource" "check_vms" {
  # 在 VM 创建之后触发
  triggers = {
    vm_ips = join(",", var.vm_ips)
  }

  provisioner "remote-exec" {

    connection {
      type        = "ssh"
      host        = "172.24.100.52"
      user        = "root"
      password    = "ggBYAmnK^^cP"
      }

    inline = [
      "bash /home/userlocal/check_vm.sh ${self.triggers.vm_ips}"
    ]
  }
}
