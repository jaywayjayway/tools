#  simple tools

-  tcp_check
-  domainctl

##  nginx template 
```
{{range $dir := lsdir "/services/web"}}
upstream {{base $dir}} {
    {{$custdir := printf "/services/web/%s/*" $dir}}{{range gets $custdir}}
    server {{.Value}}:8888; {{end}}
}

server {
    listen      80;
    server_name {{base $dir}};
    access_log   /var/log/nginx/{{base $dir}}_access_log;
    error_log    /var/log/ngin/{{base $dir}}_error_log;
    location / {
        proxy_pass {{base $dir}};
            proxy_set_header   Host             $host;
            proxy_set_header   X-Real-IP        $remote_addr;
            proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
            proxy_set_header Via    "nginx";

    }
}
{{end}}

```
###  haproxy  tempalte
```

global
    log         127.0.0.1 local2  info
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     4000
    user        haproxy
    group       haproxy
    daemon

    stats socket /var/lib/haproxy/stats

defaults
    mode                    http
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 3000

frontend main *:5000
        acl url_static       path_beg       -i /static /images /javascript /stylesheets
        acl url_static       path_end       -i .jpg .gif .png .css .js
        use_backend static          if url_static

{{range $dir := lsdir "/services/web"}}
        acl     {{base $dir}} hdr_beg(host) -i   {{base $dir}} 
        use_backend   {{base $dir}}  if  {{base $dir}}
{{end}}

backend  static
   balance     roundrobin
   server   images   10.10.0.3:80 check 



{{range $dir := lsdir "/services/web"}}
backend  {{base $dir }}
    balance     roundrobin
   {{$custdir := printf "/services/web/%s/*" $dir}}{{range gets $custdir}}
    server  {{base .Key}}  {{.Value}}:8888 check
   {{end}}
{{end}}

```

- doaminctl help 
```
#domainctl  -h 
usage: domainctl [-h] [-H HOST] [-p PORT] [-d DOMAIN | -D NAME | -i INSERT]

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  etcd server ipaddress.[default:127.0.0.1]
  -p PORT, --port PORT  etcd listen port.[default:2379]
  -d DOMAIN, --domain DOMAIN
                        show domain infomation,[ALL|all] show all domains
  -D NAME, --name NAME  Delete Domain, exaple: -D oa.quakegame.cn
  -i INSERT, --insert INSERT
                        add domain ,example: -i 'gm.quakegame.test
                        1.1.1.1,2.2.2.2; oa.quakegame.cn 3.3.3.3,4,4,4,4'
```
```
# domainctl -d all

{
  "message": {
    "/services/web/gm.quakegame.cn": {
      "server0": "10.10.0.3",
      "server1": "10.10.0.4"
    },
    "/services/web/awr.docm.dfas": {
      "server0": "234.23.3.3"
    },
    "/services/web/oa.quakegame.cn": {
      "server0": "2.2.2.2"
    },
    "/services/web/jaywaychou.com": {
      "server0": "10.10.0.3",
      "server1": "10.10.0.4"
    },
    "/services/web/xiaofuge.com": {
      "server0": "10.10.0.3",
      "server1": "10.10.0.3"
    },
    "/services/web/pay.quakegame.cn": {
      "server0": "10.10.0.3",
      "server1": "10.10.0.4"
    }
  },
  "code": 200
}

```




