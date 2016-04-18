#!/usr/bin/env python

from __future__ import unicode_literals
from optparse import OptionParser
import etcd
import sys
import json
import argparse
import datetime

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return json.JSONEncoder.default(self, obj)

class Etcd(object):
    """Configuration with etcd  Provide push, pull function."""

    def __init__(self, host='', port='', *args, **kwargs):
        self.host = host
        self.port = port

    @property
    def _conn_etcd(self):
        """connection etcd Server."""
        client = etcd.Client(host=self.host, port=self.port)
        return client

    def set_config(self, info):
        """set configuration.

        {"gm.quakegame.cn","1.1.1.1,2.2.2.2"} ===> rewriter  all domain 
        {"gm.quakegame.cn/server0",'3.3.3.3'} ===> just rewriter  server0 

        """
        client = self._conn_etcd
        domain_info = info 
        for _k,_v  in domain_info.items():
            ip_list = _v.split(',')
            if  len(_k.split('/')) > 1 :  ###  example   gm.quakegame.cn/server0 
               try:
                  _out = client.read('/services/web/%s'%(_k))
                  _out.value = ip_list[0]
                  client.update(_out)

               except Exception as e:
                  return_message = {'code': 500, 'message': str(e)}
                  return return_message
                
               continue

            try:

               client.delete('/services/web/%s'%(_k), recursive = True)

            except Exception as e:
               pass

            for _i in  range(len(ip_list)):
                try:
                    client.set('/services/web/%s/server%s'%(_k,_i),ip_list[_i])
                except Exception as e:
                    return_message = {'code': 500, 'message': str(e)}
                    return return_message

        return_message = {'code': 200, 'message': "set success"}
        return return_message


    def delete_domain(self,domain):
        """ delete domain """
        client = self._conn_etcd
        try:
            client.delete('/services/web/%s'%(domain), recursive = True)

        except Exception as e:

            return_message = {'code': 500, 'message': str(e)}

        return_message = {'code': 200, 'message': 'delete  success.'}
        return return_message



    def ip_check(self,ip):
        q = ip.split('.')
        return len(q) == 4 and len(filter(lambda x: x >= 0 and x <= 255, \
            map(int, filter(lambda x: x.isdigit(), q)))) == 4

    def _domain(self,domain=""):
        """ get domain info with dic """
        domains = {} 
        try:
            client = self._conn_etcd
            dom = domain.split() 
            if not  len(dom):
                domain_directory=client.get("/services/web")
                for  result  in domain_directory.children:
                    domains.setdefault(result.key,{})
            else:
                for  d in dom:
                    domains.setdefault("/services/web/"+d,{})
            for _d  in  domains:
                servers_directory  = client.get(_d)
                for _s  in  servers_directory.children:
                    domains[_d][_s.key.split('/')[-1]]=_s.value
                
            return_message =  {'code': 200, 'message':domains}

        except Exception as e:
            return_message = {'code': 500, 'message': '%s not found' %domain}
            #return_message = {'code': 500, 'message': str(e)}

        return  return_message

def ops():
    parser = argparse.ArgumentParser(prog="domainctl")
    parser.add_argument('-H', "--host", action='store', type=str, default='127.0.0.1',help="etcd server ipaddress.[default:127.0.0.1]")
    parser.add_argument('-p', "--port", action='store', type=int, default=2379,help="etcd listen port.[default:2379]")
    group = parser.add_mutually_exclusive_group()
    #group.add_argument('-H', "--host", action='store', type=str, default='127.0.0.1',help="etcd server ipaddress.[default:127.0.0.1]")
    #group.add_argument('-p', "--port", action='store', type=int, default=2379,help="etcd listen port.[default:2379]")
    group.add_argument('-d', "--domain",action='store', type=str, default='ALL',help="show domain infomation,[ALL|all] show all domains")
    group.add_argument('-D',"--name",action='store', type=str,help="Delete Domain, exaple: -D oa.quakegame.cn")
    group.add_argument('-i', "--insert",action='store', type=str,help="add domain ,example:  \
    -i \'gm.quakegame.test  1.1.1.1,2.2.2.2; oa.quakegame.cn 3.3.3.3,4,4,4,4\'")
    return parser.parse_args()

def json_encode(value):
    """Python object to JSON"""
    return json.dumps(value, cls=ComplexEncoder).replace("</", "<\\/")

def json_decode(value):
    """JSON to Python object"""
    return escape.json_decode(value)

def ip_check(ip):
    q = ip.split('.')
    return len(q) == 4 and len(filter(lambda x: x >= 0 and x <= 255, \
        map(int, filter(lambda x: x.isdigit(), q)))) == 4

def info_to_dic(value):
    """trancefort  info to  dic
    
    exmaple: 
            'gm.quakegame.test  1.1.1.1,2.2.2.2' --->  {'gm.quakegame.test':'1.1.1.1,2.2.2.2'}
    """
    Domain_Info = {}    
    
    _tmp =  value.split(';') 
    for   _k in  _tmp:
        Domain_Info.setdefault(_k.split()[0],_k.split()[-1])

    for _v in  Domain_Info.values():
        for ip in _v.split(','):
            if not ip_check(ip):
                exit(json_encode({'code': 500, 'message': '%s is not IP' %ip}))
    return   Domain_Info

def main():
    if  not sys.argv[1:]:
        exit("please use  %s -h or --help" %sys.argv[0])
    options  = ops()
    client=Etcd(options.host,options.port)

    if options.insert and client:
        data = client.set_config(info_to_dic(options.insert))
        return json_encode(data)

    if options.name and client:
        data = client.delete_domain(options.name)
        return json_encode(data)

    if  options.domain.upper() == "ALL":
        data = client._domain()
        return json_encode(data)
    else:
        data = client._domain(options.domain)
        return json_encode(data)

if __name__ == "__main__":
    print(main())
