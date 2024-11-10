provider "null" {}

# module路径
locals {
  module_path = path.module
}

# 生成网络的 XML 内容
locals {
  network_xml_content = <<-EOT
    <!-- 你的动态生成的 XML 内容 -->
    <network>
      <name>${var.name}</name>
      <forward mode='nat'>
        <nat>
          <port start='1024' end='65535'/>
        </nat>
      </forward>
      <bridge name='virbr1' stp='on' delay='0'/>
      <ip address='192.168.100.1' netmask='255.255.255.0'>
        <dhcp>
          <range start='192.168.100.2' end='192.168.100.254'/>
        </dhcp>
      </ip>
    </network>
  EOT
}

# 开启网络
resource "null_resource" "start_network" {
  # 根据 create_network 变量决定是否执行
  count = var.judgement ? 1 : 0

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      xml_path="${local.module_path}/${var.name}.xml"
      echo "${local.network_xml_content}" > "$xml_path"
      virsh net-define "$xml_path"
      virsh net-start "${var.name}"
      virsh net-autostart "${var.name}"
    EOT
  }
}