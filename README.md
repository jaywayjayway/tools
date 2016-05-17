#  simple tools

-  tcp_check
-  domainctl


## haproxy  template 
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

frontend etcd
    bind 192.168.0.16:2379
    mode tcp
    option tcplog
    default_backend etcd
    log 127.0.0.1 local3

frontend main *:5000
        acl url_static       path_beg       -i /static /images /javascript /stylesheets
        acl url_static       path_end       -i .jpg .gif .png .css .js
        use_backend static          if url_static
{{range $server_dir := lsdir  "/services"}}
{{$business_dir  := printf  "/services/%s" $server_dir}}
{{range $dir := lsdir  $business_dir}}
    {{$domain_dir := printf "%s/%s/"  $business_dir $dir}}
    {{range $name  := lsdir   $domain_dir}}
        acl     {{base $name}} hdr_beg(host) -i   {{base $name}} 
        use_backend   {{base $name}}  if  {{base $name}}
    {{end}}
{{end}}
{{end}}

backend etcd
    balance roundrobin
    fullconn 1024
    server etcd1 10.10.0.1:2379 check port 2379 inter 300 fall 3
    server etcd2 10.10.0.3:2379 check port 2379 inter 300 fall 3
    server etcd3 10.10.0.4:2379 check port 2379 inter 300 fall 3

backend  static
   balance     roundrobin
   server   images   10.10.0.3:80 check 


{{range $server_dir := lsdir  "/services"}}
{{$business_dir  := printf  "/services/%s" $server_dir}}
{{range $dir := lsdir  $business_dir}}
    {{$domain_dir := printf "%s/%s/"  $business_dir $dir}}
    {{range $name  := lsdir   $domain_dir}}
      {{$server := printf "%s/%s/%s/*" $business_dir $dir $name}}
backend  {{$name}}        
    balance   roundrobin
        {{range gets $server}}
        server {{base .Key}}  {{.Value}}:4001 check port 4001 inter 300 fall 3
        {{end}}
    {{end}}
{{end}}
{{end}}

```

##  nginx (LB) template 
```
{{range $_dir := lsdir  "/services"}}
{{$service_dir  := printf  "/services/%s" $_dir}} 
    {{range $business_dir := lsdir  $service_dir}}
        {{$domain_dir := printf "%s/%s/"  $service_dir $business_dir}}
        {{range $name  := lsdir  $domain_dir}}

        {{$server := printf "%s/%s/%s/*" $service_dir $business_dir  $name}}
        
upstream  {{$name}} {
 {{range gets $server}}
    server {{.Value}}:4001; 
        {{end}}
}

server {
    listen     5001; 
    server_name {{$name}};
    location / {
        proxy_pass http://{{$name}};
            proxy_set_header   Host             $host;
            proxy_set_header   X-Real-IP        $remote_addr;
            proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
            proxy_set_header Via    "nginx";
    }
}

        {{end}}
    {{end}}
{{end}}


```

## nginx ( web server ) template 
```
{{range $_dir := lsdir  "/services"}}
{{$service_dir  := printf  "/services/%s" $_dir}} 
    {{range $business_dir := lsdir  $service_dir}}
        {{$domain_dir := printf "%s/%s/"  $service_dir $business_dir}}
        {{range $name  := lsdir  $domain_dir}}
server {
   listen      4001;
   server_name {{base $name}};
   index index.html default.htm index.htm index.php;

   root  /data/wwwroot/{{base $name}};
   access_log /var/log/nginx/{{base $name}}-access_log main;
   include  gameweb.cfg;
}
        {{end}}
    {{end}}
{{end}}

```

- doaminctl help 

```
[root@nn1 tools]# domainctl -h 
usage: domainctl [-h] [-H HOST] [-p PORT] [-P PLATFORM] [-b BUSINESS] [-s]
                 [-d DOMAIN | -D NAME | -i INSERT]

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  etcd server ipaddress.[default:127.0.0.1]
  -p PORT, --port PORT  etcd listen port.[default:2379]
  -P PLATFORM, --platform PLATFORM
                        kinds of platform.
  -b BUSINESS, --business BUSINESS
                        kinds of business.
  -s, --show            show all domains
  -d DOMAIN, --domain DOMAIN
                        search the domain infomation
  -D NAME, --name NAME  Delete Domain,example: -D oa.quakegame.cn
  -i INSERT, --insert INSERT
                        add domain,example: -i 'gm.quakegame.test
                        1.1.1.1,2.2.2.2; oa.quakegame.cn 3.3.3.3,4,4,4,4'

``` 

- show all aviable domains 


```
[root@nn1 tools]# domainctl -s  | jq .
{
  "message": {
    "/services/17kxgame/web/cc.17kxgame.cn": [
      "1.1.1.1",
      "1.1.1.12"
    ],
    "/services/kugou/web/oa.quakegame.cn": [
      "1.1.1.4",
      "1.1.1.5"
    ],
    "/services/kugou/web/test.quakgame.cn": [
      "1.1.1.1",
      "1.1.1.2"
    ],
    "/services/17kxgame/web/dzz.17kxgame.cn": [
      "1.1.1.1",
      "1.1.1.2"
    ]
  },
  "code": 200
}


```


- add  a new domain 

```
[root@nn1 tools]# domainctl  -P 17kxgame -b web -i "add.17kxgame.cn 1.1.1.1,1.1.1.2,1.1.1.3"
{"message": "set success", "code": 200}

```

- delete a domain


```
[root@nn1 tools]# domainctl  -P 17kxgame -b web -D dzz.17kxgame.cn
{"message": "delete  success.", "code": 200}

```

- search the domain 

```
[root@nn1 tools]# domainctl -d  dzz.17kxgame.cn  | jq . 
{
  "message": {
    "/services/17kxgame/web/dzz.17kxgame.cn": [
      "1.1.1.1",
      "1.1.1.2"
    ]
  },
  "code": 200
}
[root@nn1 tools]# domainctl -d  www.google.com  | jq . 
{
  "message": "【www.google.com】 not found ",
  "code": 500
}

```





