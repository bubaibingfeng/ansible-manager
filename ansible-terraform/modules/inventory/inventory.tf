resource "local_file" "hosts_file" {
  content  = templatefile("${path.module}/hosts.tpl", {
    master_hostnames = var.master_hostnames
    node_hostnames   = var.node_hostnames
    master_ips       = var.master_ips
    node_ips         = var.node_ips
  })
  filename = "${path.module}/hosts.ini"
}


resource "null_resource" "setup_remote" {
  depends_on = [local_file.hosts_file]

  provisioner "remote-exec" {
    inline = [
      "cp -r /home/admin/k3s-clusters-mgt/inventory/demo-0124 /home/admin/k3s-clusters-mgt/inventory/${var.cluster_name}"
    ]

    connection {
      type        = "ssh"
      user        = "root"
      private_key = file("~/.ssh/id_rsa")
      host        = "172.24.100.52"
    }
  }

  provisioner "file" {
    source      = local_file.hosts_file.filename
    destination = "/home/cjf/k3s-clusters-mgt/inventory/${var.cluster_name}/hosts.ini"

    connection {
      type        = "ssh"
      user        = "root"
      private_key = file("~/.ssh/id_rsa")
      host        = "172.24.100.52"
    }
  }
}
