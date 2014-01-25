#!/usr/bin/python

#################################################################
#                                                               #
#   XML-RPC Server                                              #
#   Projekt zaliczeniowy z Pracowni Jezykow Skryptowych         #
#   Uniwersytet Jagiellonski, Krakow                            #
#                                                               #
#   Serwer XML-RPC                                              #
#   (c) 2014 Marcin Radlak                                      #
#   marcin.radlak@uj.edu.pl                                     #
#   http://marcinradlak.pl                                      #
#                                                               #
#################################################################

import getopt
import sys
import shelve
import uuid
import base64
import socket
import Cookie
from SimpleXMLRPCServer import *  

class Host:
  def __init__(self):
    self.db = shelve.open('hosts.shv')

    # lista autoryzowanych hostow serwera
    validconfig = { 'email@address.com': 'vaikings' }

    for email, host in validconfig.items():
      self.generate_id(email, host)

  # generujemy id dla kazdego polaczonego hosta
  def generate_id(self, email, host):
    host_id = None

    if host not in self.db:
      myNamespace = uuid.uuid3(uuid.NAMESPACE_URL, host)
      host_id = str(uuid.uuid3(myNamespace, email)) 

      self.db[host] = (host, host_id, email)
      self.db[host_id] = (host, host_id, email)

    else:
      (host, host_id, email) = self.db[host]

    return host_id

  def sign_in(self, id):
    if id in self.db:
      return self.db[id]
    return (None, None, None)

  def __del__(self):
    self.db.close()

class RequestHandler(SimpleXMLRPCRequestHandler):
  def set_up_cookie(self, key = None, value = None):
    if key:
      cookie = Cookie.SimpleCookie()
      cookie[key] = value

      tags = {
        'expires': 30*24*60*60,
        'path': '/RPC2/',
        'comment': 'comment!',
        'domain': '.localhost.local',
        'max-age': 30*24*60*60,
        'secure': '',
        'version': 1
      } 

      for attr, val in tags.items():
        cookie[key][attr] = val
                            
      if cookie not in self.cookies:
        self.cookies.append(cookie)
                 
  # Interpretuje wszystkie request'y HTTP jako wywolania XML-RPC  
  # Obsluga cookies'ow         
  def do_POST(self):
    if not self.is_rpc_path_valid():
      self.report_404("404 Unknown path.")
      return

    try:      
      data = []
      # czytamy porcjami max 10mb w celu unikniecia blokady serwera
      max_size = 10 * 1024 * 1024
      real_size = int(self.headers["content-length"])
      
      while real_size:
        size = min(real_size, max_size)
        data.append(self.rfile.read(size))
        real_size -= len(data[-1])
        data = ''.join(data)

        response = self.server._marshaled_dispatch(data, getattr(self, '_dispatch', None))
    except:
      # Internal server error 
      self.send_response(500)
      self.end_headers()

    else:
      self.send_response(200)
      self.send_header("Content-type", "text/xml")
      self.send_header("Content-length", str(len(response)))

      # przesylanie cookies
      if self.cookies:
        for cookie in self.cookies:
          self.send_header('Set-Cookie', cookie.output(header = ""))
            
      self.end_headers()
      self.wfile.write(response)
      self.wfile.flush()
      self.connection.shutdown(1)

  def authenticate(self, id):
    sk = Host()
    return sk.sign_in(id)

  def authenticate_client(self):
    auth = False

    if self.headers.has_key('Authorization'):
      (enctype, encstr) =  self.headers.get('Authorization').split()
      (email, host) = base64.standard_b64decode(encstr).split(':')
      (auth_machine, auth_id, auth_email) = self.authenticate(host)

      if email == auth_email:
        auth = True
        print "Authenticated"

        if auth_id:
          self.set_up_cookie('ID', auth_id)
                    
    elif self.headers.has_key('ID'):
      id =  self.headers.get('ID')
      (auth_machine, auth_id, auth_email) = self.authenticate(id)

      if auth_id :
        auth = True
        print "Authenticated"
        
    else:
      print 'Authentication failed'

    return auth

  # obsluga web service'ow
  def _dispatch(self, service, vars):    
    self.cookies = []        
    auth = self.authenticate_client()   

    if service == 'add':                
      (var1, var2) = vars    
      return WebServices().add(var1, var2)
    elif service == 'minus':                
      (var1, var2) = vars    
      return WebServices().minus(var1, var2)
    elif service == 'println':                  
      return WebServices().println(vars)
    else:
      return "Service " + service + " doesn't exist."

# dostepne web service's
class WebServices:
  def add(self, var1, var2):
    s = var1 + var2
    return str(var1) + " + " + str(var2) + " = " + str(s)

  def minus(self, var1, var2):
    s = var1 - var2
    return str(var1) + " - " + str(var2) + " = " + str(s)

  def println(self, var):
    return var

def usage():
  print "-----------------------------------------------------------------------------------------------\n"
  print " XML-RPC Server\n\n"
  print " Uzycie: program [-s SERWER] [-p PORT] [--help|-h]\n\n"
  print " Program do automatycznej synchronizacji plikow na lokalnym serwerze ze zdalnym serwerem FTP.\n"
  print " Program porownuje pliki i foldery zawarte w katalogu podanym przez uzytkownika z zawartoscia\n"
  print " na serwerze FTP. Program rozroznia poszczegole przypadki zawartosci:\n"
  print " 1. Jesli plik znajduje sie na serwerze lokalnym, a na serwerze FTP nie, to zostanie wyslany.\n"
  print " 2. Jesli plik znajduje sie na serwerze FTP, a na serwerze lokalnym nie, to zostanie usuniety.\n"
  print " 3. Jesli plik znajduje sie na serwerze lokalnym oraz a na serwerze FTP, to zostana porownane\n"
  print " wersje. Jesli wersja pliku lokalnego okaze sie nowsza od zdalnej to plik zostanie nadpisany.\n"
  print "-----------------------------------------------------------------------------------------------\n"

# glowna funkcja
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hs:p:", ["help"])

    serv = "localhost"
    port = 8088

    for opt, val in opts:
      if opt in ("-h", "--help"):
        usage()
        sys.exit(0)
      elif opt == "-s":
        serv = val
      elif opt == "-p":
        port = int(val)

    server = SimpleXMLRPCServer((serv, port), RequestHandler, True, True)
    server.register_introspection_functions()
    server.serve_forever()

  except getopt.GetoptError as err:
    print str(err)
    usage()
    sys.exit(1)
  except ValueError:
    usage()
    sys.exit(1)
  except KeyboardInterrupt:
    sys.exit(0)

# main
if __name__ == '__main__':
  main()
