[master]
%{ for index, ip in master_ips ~}
${master_hostnames[index]} ansible_host=${ip}
%{ endfor ~}

[node]
%{ for index, ip in node_ips ~}
${node_hostnames[index]} ansible_host=${ip}
%{ endfor ~}

[k3s_cluster:children]
master
node
