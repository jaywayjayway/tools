#!/usr/bin/env python
#coding:utf-8 

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

    def __init__(self, host='', port='', platform='',business='',*args, **kwargs):
        self.host = host
        self.port = port
        self.platform = platform
        self.business = business
        self.prefix = ''
        if self.platform and self.business:
            self.prefix ='/'.join([self.platform,self.business])
        elif self.platform :
            self.prefix = self.platform
        self.client = self._conn_etcd
        self.check = self.key_check()
        self.msg = {}

    @property
    def _conn_etcd(self):
        """connection etcd Server."""
        try:
            client = etcd.Client(host=self.host, port=self.port)
            return client
        except Exception as e:
            return_message = {'code': 500, 'message': str(e)}
            return return_message

    def show_all_domain(self):
        client = self.client
        platform_list = {} 
        _platform =  []
        for p in client.get('/services/')._children:
             _platform.append(p['key'].split('/')[-1])
        #for  P  in  platform_list.keys(): 
        for  P  in  _platform: 
              for b in  client.get('/services/%s' %P)._children:
                    B=b['key'].split('/')[-1]
                    #platform_list[P].setdefault(b['key'].split('/')[-1],[])
                    for i in client.get(b['key'])._children:
                        S = i['key'].split('/')[-1]
                        #platform_list[p][(b['key'].split('/')[-1])].append(s)
                        #platform_list[p][(b['key'].split('/')[-1])].append(i['key'].split('/')[-1])
                        #print P,B,S
                        platform_list.setdefault('/services/%s/%s/%s' %(P,B,S), [])
                        #return platform_list
                        for IP  in client.get('/services/%s/%s/%s' %(P,B,S))._children:
                            platform_list['/services/%s/%s/%s' %(P,B,S)].append(IP['value'])

        return platform_list

 
    def search_domain(self,path,domain):
        key_list = [] 
        for i in self.client.get(path)._children:
            key_list.append (i['key'])
        for key  in key_list:
            if domain == key.split('/')[-1]:
                IP = []
                msg = {} 
                for _d in self.client.get(key)._children:
                    IP.append(_d['value'])
                msg.setdefault(key,IP)
                self.msg = msg  
                #print msg
                #return {"code":200,"message":msg}
            if not self.msg:
                self.search_domain(key,domain)


    def set_config(self, info):
        """set configuration.

        {"gm.quakegame.cn","1.1.1.1,2.2.2.2"} ===> rewriter  all domain 
        {"gm.quakegame.cn/server0",'3.3.3.3'} ===> just rewriter  server0 

        """
        client = self.client
        domain_info = info 
        for _k,_v  in domain_info.items():
            ip_list = _v.split(',')
            if  len(_k.split('/')) > 1 :  ###  example   gm.quakegame.cn/server0 
               try:
                  _out = client.read('/services/%s/%s'%(self.prefix,_k))
                  _out.value = ip_list[0]
                  client.update(_out)

               except Exception as e:
                  return_message = {'code': 500, 'message': str(e)}
                  return return_message
                
               continue

            try:

               client.delete('/services/%s/%s'%(self.prefix,_k), recursive = True)

            except Exception as e:
               pass

            for _i in  range(len(ip_list)):
                try:
                    client.set('/services/%s/%s/server%s'%(self.prefix,_k,_i),ip_list[_i])
                except Exception as e:
                    return_message = {'code': 500, 'message': str(e)}
                    return return_message

        return_message = {'code': 200, 'message': "set success"}
        return return_message


    def delete_domain(self,domain):
        """ delete domain """
        client = self.client
        try:
            client.delete('/services/%s/%s'%(self.prefix,domain), recursive = True)

        except Exception as e:

            return_message = {'code': 500, 'message': str(e)}

        return_message = {'code': 200, 'message': 'delete  success.'}
        return return_message


    def key_check(self):
        
        client = self.client
        try:
            client.get('/services/%s' % (self.prefix))
            return 

        except Exception as e:
            return ({'code': 500, 'message': str(e)})

    def ip_check(self,ip):
        q = ip.split('.')
        return len(q) == 4 and len(filter(lambda x: x >= 0 and x <= 255, \
            map(int, filter(lambda x: x.isdigit(), q)))) == 4

    def _domain(self):
        """ get domain info with dic """
        domains = {} 
        client = self.client
        if self.platform and self.business: 
            try:
                domain_directory=client.get("/services/%s" %(self.prefix))
                for result  in domain_directory.children:
                    domains.setdefault(result.key,[])
                #print "#"*10 ,domains
                for business in  domains.keys():
                    for server  in client.get(business)._children:
                        domains[business].append(server['value'])

            except Exception as e:
                return_message = {'code': 500, 'message': str(e)}
                return  return_message
            
        elif self.platform:
            try:
                business_directory=client.get("/services/%s" %(self.platform))
                for business  in  business_directory.children:
                    for domain in  client.get(business.key).children:
                         domains.setdefault(domain.key,[])
    
                for  domain in domains.keys():
                     for IP in client.get(domain)._children:
                         domains[domain].append(IP['value'] )
                
            except Exception as e:
                return_message = {'code': 500, 'message': str(e)}
                return  return_message

        else:
            domains = self.show_all_domain()
            
        return_message =  {'code': 200, 'message':domains}
        return  return_message


def ops():
    parser = argparse.ArgumentParser(prog="domainctl")
    parser.add_argument('-H', "--host", action='store', type=str, default='127.0.0.1',help="etcd server ipaddress.[default:127.0.0.1]")
    parser.add_argument('-p', "--port", action='store', type=int, default=2379,help="etcd listen port.[default:2379]")
    parser.add_argument('-P', "--platform", action='store',type=str,help="kinds of platform.")
    parser.add_argument('-b', "--business", action='store',type=str,help="kinds of business.")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('-s',"--show", action="store_true",help="show all domains")
    group.add_argument('-d', "--domain",action='store', type=str,help="search  the domain infomation")
    group.add_argument('-D',"--name",action='store', type=str,help="Delete Domain,example: -D oa.quakegame.cn")
    group.add_argument('-i', "--insert",action='store', type=str,help="add domain,example: -i \'gm.quakegame.test  1.1.1.1,2.2.2.2; oa.quakegame.cn 3.3.3.3,4,4,4,4\'")
    #return parser.parse_args()
    return parser

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
    parser = ops()
    if  not sys.argv[1:]:
       return  parser.print_help()
            
    options = parser.parse_args()
    client=Etcd(options.host,options.port,options.platform,options.business)

    if isinstance(client.client,dict):
        return  json_encode(client.client)

    ###  Show  Domain ####
    if options.show:
        data = client._domain()
        return json_encode(data)

    ###  insert  Domain ###
    if options.insert and client:

        if not (options.platform and options.business):
            return json_encode({'code': 500, 'message': 'please  set platform and  business'})

        if  client.check:
            return  json_encode(client.check)

        data = client.set_config(info_to_dic(options.insert))
        return json_encode(data)

    ###  Delete  Domain ###
    if options.name and client:

        if not (options.platform and options.business):
            return json_encode({'code': 500, 'message': 'please  set platform and  business'})

        if  client.check:
            return  json_encode(client.check)
        data = client.delete_domain(options.name)
        return json_encode(data)

    ### Search Domain ####
    if options.domain and client:
        client.search_domain(path='/services/',domain=options.domain)
        if client.msg :
            data = {"code":200,"message":client.msg}
        else:
            data = {"code":500,"message":"【%s】 not found " %(options.domain)}
        return json_encode(data)
            
if __name__ == "__main__":
    print(main())
