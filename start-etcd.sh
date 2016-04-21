#!bin/bash 
HOSTNAME=`/usr/bin/hostname`
nohup /usr/bin/etcd -name niub1  \
--data-dir  /var/lib/etcd/  \
-initial-advertise-peer-urls http://10.10.0.1:2380 \
-listen-peer-urls http://10.10.0.1:2380 \
-listen-client-urls http://10.10.0.1:2379,http://127.0.0.1:2379 \
-advertise-client-urls http://10.10.0.1:2379 \
-initial-cluster-token etcd-cluster \
-initial-cluster niub1=http://10.10.0.1:2380,niub2=http://10.10.0.3:2380,niub3=http://10.10.0.4:2380 \
-initial-cluster-state new   >> /tmp/etcd.log 2>&1  & 

