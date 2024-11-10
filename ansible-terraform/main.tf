# main.tf


# 创建并调整虚拟机磁盘大小
module "resize_disk" {
  source = "./modules/resized_disk"
  count = length(var.vm_name)

  # 源镜像路径/网络地址
  base_image_path = "${var.base_image}"
  
  # 新镜像路径，调用vm_name变量作为名称
  new_image_path = "/data/base/qcow2/${var.vm_name[count.index]}.qcow2"
  
  # 扩展磁盘容量
  additional_size = "${var.additional_size}" # 单位GB
}


# 创建cloudinit配置文件
module "cloudinit" {
  source = "./modules/cloudinit"
  count = length(var.vm_name)

  # 配置文件名称，调用vm_name变量
  filename = "${var.vm_name[count.index]}.cfg"

  # 配置vm的hostname，调用vm_name变量
  hostname = "${var.vm_name[count.index]}"

  # 配置vm的ssh密钥
  ssh_keys = var.ssh_public_keys

  # 设置用于ssh登陆的用户名
  username = var.username

  # 设置非root登录密码
  sha512password = var.password

  # 设置静态ip
  static_ip = var.static_ip[count.index]

  # 设置子网掩码
  subnet_mask = var.subnet_mask

  # 设置网关
  gateway_ip = var.gateway_ip

  # 设置DNS server
  dns_servers = var.dns_servers
}

# 创建cloudinit可挂载镜像
module "cloudinit_image" {
  # 等待cloudinit配置文件模块完成后执行
  depends_on = [ module.cloudinit ]
  source = "./modules/cloudinit_img"
  count = length(var.vm_name)
  
  # 调用cloudinit模块的输出文件路径
  base_file = "${element(module.cloudinit, count.index).cloudinit_filepath}"
  
  # 文件名设置为vm_name_cloudinit.img
  name = "${var.vm_name[count.index]}_cloudinit"
}

# 创建集群专属网络
module "network" {
  judgement = var.network_judgement
  source  = "./modules/network"  # 指定模块的相对路径或远程 URL
  # 目前暂时采用nat+DHCP方式
  name  = "${var.network_name}"  # 替换为你想要的网络名称
}

# # 创建给ansible的inventory文件
# module "inventory" {
#   source          = "./modules/inventory"
#   master_hostnames = var.master_hostnames
#   node_hostnames   = var.node_hostnames
#   master_ips       = var.masters_ips
#   node_ips         = var.nodes_ips
#   cluster_name     = var.cluster_name 
# }


# 创建虚拟机
resource "null_resource" "create_vm" {
  depends_on = [ module.cloudinit,module.cloudinit_image,module.network,module.resize_disk ]
  count = length(var.vm_name)
  triggers = {
    # 这个触发器会导致 provisioner 每次运行
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      virt-install \
        --name ${var.vm_name[count.index]} \
        --virt-type kvm \
        --memory ${var.memory} \
        --vcpus ${var.vcpus} \
        --boot hd,menu=on \
        --disk path=${module.resize_disk[count.index].resized_image_path},format=qcow2,bus=virtio \
        --disk path=${module.cloudinit_image[count.index].cloudinit_img_path},format=qcow2,bus=virtio \
        --os-variant ubuntu22.04 \
        --graphics vnc,listen=0.0.0.0 \
        --network bridge=br0,model=virtio \
        --noautoconsole
    EOT
  }
}

# 查看虚拟机连通性
module "check_vm_status" {
  depends_on = [ null_resource.create_vm ]
  source = "./modules/check_vm_status"
  vm_ips = var.static_ip
}


# # 创建K3S集群
# module "ansible" {
#   source          = "./modules/ansible"
#   depends_on = [ module.check_vm_status ]
#   cluster_name    = var.cluster_name
# }
