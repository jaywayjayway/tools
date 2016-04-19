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





