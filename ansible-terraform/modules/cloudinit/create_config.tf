# 声明创建cloudinit的cfg文件
resource "local_file" "cloudinit_cfg" {
  content = <<EOF
#cloud-config
hostname: ${var.hostname}

users:
  - name: ${var.username}
    groups: sudo
    shell: /bin/bash
    ssh-authorized-keys:
    %{ for key in var.ssh_keys ~}
      - ${key} 
    %{ endfor ~}

  - name: root
    groups: sudo
    shell: /bin/bash
    password: 121212
    chpasswd: { expire: False }
    ssh_pwauth: True
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
chpasswd:
  list: |
     ${var.username}:HTuser123
     root:121212
  expire: False
ssh_pwauth: true
timezone: ${var.timezone}

packages:
%{ for package in var.packages ~}
  - ${package}
%{ endfor ~}


#cloud-config

write_files:
  - path: /etc/netplan/50-cloud-init.yaml
    content: |
      # This file is generated from information provided by the datasource.  Changes
      # to it will not persist across an instance reboot.  To disable cloud-init's
      # network configuration capabilities, write a file
      # /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg with the following:
      # network: {config: disabled}
      network:
        ethernets:
            enp1s0:
                dhcp4: false
                addresses:
                  - ${var.static_ip}/${var.subnet_mask}  # 替换为您的静态IP和子网掩码
                gateway4: ${var.gateway_ip} # 替换为您的网关IP
                nameservers:
                  addresses: [${join(", ", formatlist("\"%s\"", var.dns_servers))}]  # 替换为您的DNS服务器地址
                match:
                    name: enp1s0
                set-name: enp1s0
        version: 2

runcmd:
  - netplan apply


EOF

  filename = "cloudinit/cloudinit_config/${var.filename}"
}

# 输出生成成功的语句并给出路径
resource "null_resource" "output" {
  provisioner "local-exec" {
    command = "echo 'cloudinit config generated!';echo 'cloudinit_filepath = ${local_file.cloudinit_cfg.filename}'"
  }
}

# 输出文件路径
output "cloudinit_filepath" {
  value = local_file.cloudinit_cfg.filename 
}