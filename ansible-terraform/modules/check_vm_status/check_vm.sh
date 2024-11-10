#!/bin/bash
# check-vm-status.sh

# 读取从 Terraform 传入的 IP 地址列表
IFS=$'\n' read -r -d '' -a ip_array <<< "$1"

all_up=true

# 循环检查每个 IP 地址
for ip in "${ip_array[@]}"; do
    echo "Checking VM at IP: $ip"
    count=0
    while ! ping -c 1 $ip &> /dev/null; do
        count=$((count + 1))
        if [ $count -ge 24 ]; then
            echo "Failed to reach VM at IP: $ip after several attempts."
            all_up=false
            break
        fi
        echo "Waiting for VM at IP: $ip ..."
        sleep 10
    done

    if [ "$all_up" = false ]; then
        break
    fi

    echo "VM at IP: $ip is up and running."
done

if [ "$all_up" = true ]; then
    echo "All VMs are up and running."
else
    echo "Some VMs are not reachable."
    exit 1
fi
