#!/usr/bin/env python2.6

import os
import base64
import xmlrpclib
import urllib2
import cookielib

class CookieAuthXMLRPCTransport(xmlrpclib.Transport):
    """ xmlrpclib.Transport that sends basic HTTP Authentication"""

    user_agent = '*py*'
    credentials = ()
    cookiefile = 'cookies.lwp'
        
    def send_basic_auth(self, connection):
        """Include HTTP Basic Authentication data in a header"""
        
        auth = base64.encodestring("%s:%s"%self.credentials).strip()
        auth = 'Basic %s' %(auth,)
        connection.putheader('Authorization',auth)

    def send_cookie_auth(self, connection):
        """Include Cookie Authentication data in a header"""
        
        cj = cookielib.LWPCookieJar()
        cj.load(self.cookiefile)

        for cookie in cj:
            if cookie.name == 'UUID':
                uuidstr = cookie.value
            connection.putheader(cookie.name, cookie.value)

    ## override the send_host hook to also send authentication info
    def send_host(self, connection, host):
        xmlrpclib.Transport.send_host(self, connection, host)
        if os.path.exists(self.cookiefile):
            self.send_cookie_auth(connection)
        elif self.credentials != ():
            self.send_basic_auth(connection)
                    
    def request(self, host, handler, request_body, verbose=0):
        # dummy request class for extracting cookies 
        class CookieRequest(urllib2.Request):
            pass
            
        # dummy response class for extracting cookies 
        class CookieResponse:
            def __init__(self, headers):
                self.headers = headers
            def info(self):
                return self.headers 

        crequest = CookieRequest('http://'+host+'/')
            
        # issue XML-RPC request
        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        self.send_user_agent(h)
        
        # creating a cookie jar for my cookies
        cj = cookielib.LWPCookieJar()
                        
        self.send_content(h, request_body)
            
        errcode, errmsg, headers = h.getreply()

        cresponse = CookieResponse(headers)
        cj.extract_cookies(cresponse, crequest)

        if len(cj) >0 and self.cookiefile != None:
            cj.save(self.cookiefile)
                
        if errcode != 200:
            raise ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        self.verbose = verbose

        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None
                
        return self._parse_response(h.getfile(), sock)

def getXmlrpcClient(server_uri, auth = ()):
    """ this will return an xmlrpc client which supports
    basic authentication/authentication through cookies 
    """

    trans = CookieAuthXMLRPCTransport()
    if auth!= ():
        trans.credentials = auth
    client = xmlrpclib.Server(server_uri, transport=trans, verbose=False)
    
    return client

if __name__ == "__main__":
    email = 'email@address.com'
    machine_name = 'vaikings'
    
    client = getXmlrpcClient('http://localhost:8088', (email,machine_name))
#    client = getXmlrpcClient('http://localhost:8088')
    inputstr1 = "hello"
    inputstr2 = "world"

    try:
        retstr = client.hello_world(inputstr1, inputstr2)
        print retstr

        print client.hey('hey')
    except Exception, e:
        print e