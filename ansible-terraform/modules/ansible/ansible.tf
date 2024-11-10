resource "null_resource" "create_cluster_operations" {
  provisioner "remote-exec" {
    inline = [
      "cd /home/admin/k3s-clusters-mgt/inventory",
      "git add .",
      "git commit -m 'create cluster ${var.cluster_name} from terraform at 172.23.2.10'",
      "git push origin main",
      "cd /home/admin/k3s-clusters-mgt",
      "./k3s-mgr create --cluster ${var.cluster_name}"
      
    ]

    connection {
      type        = "ssh"
      host        = "172.24.100.52"
      user        = "root"
      password    = "ggBYAmnK^^cP"
    }
  }
}
