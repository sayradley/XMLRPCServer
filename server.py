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

  def __del__(self):
    self.db.close()

  # generujemy id dla kazdego polaczonego hosta
  def generate_id(self, email, password):
    host_id = None

    if email not in self.db:
      name = uuid.uuid3(uuid.NAMESPACE_URL, email)
      host_id = str(uuid.uuid3(name, email)) 

      self.db[email] = (email, password, host_id)
      self.db[host_id] = (email, password, host_id)

    else:
      (email, password, host_id) = self.db[email]

    return host_id

  def sign_in(self, id):
    if id in self.db:
      return self.db[id]
    return (None, None, None)
  
class RequestHandler(SimpleXMLRPCRequestHandler):
  def set_up_cookie(self, key = None, value = None):
    if key:
      cookie = Cookie.SimpleCookie()
      cookie[key] = value

      tags = {
        'expires': 30 * 24 * 60 * 60,
        'path': '/RPC2/',
        'comment': '',
        'domain': '.localhost.local',
        'max-age': 30 * 24 * 60 * 60,
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
    host = Host()
    return host.sign_in(id)

  def register(self, email, password):
    host = Host()
    host.generate_id(email, password)

  def authenticate_client(self):
    auth = False

    if self.headers.has_key('signin'):
      (etype, e) =  self.headers.get('signin').split()
      (email, password) = base64.standard_b64decode(e).split(':')
      (auth_email, auth_password, auth_id) = self.authenticate(email)

      if email == auth_email and password == auth_password:
        auth = True
        print "Host '" + auth_email + "' authenticated."

        if auth_id:
          self.set_up_cookie('ID', auth_id)

    elif self.headers.has_key("register"):
      print "Registering new host..."
      (etype, e) =  self.headers.get('register').split()
      (email, password) = base64.standard_b64decode(e).split(':')
      self.register(email, password)  
      (auth_email, auth_password, auth_id) = self.authenticate(email)  

      if email == auth_email and password == auth_password:
        auth = True 
        self.set_up_cookie('ID', auth_id)
        print "Host '" + auth_email + "' registered and authenticated."
                    
    elif self.headers.has_key('ID'):
      id =  self.headers.get('ID')
      (auth_email, auth_password, auth_id) = self.authenticate(id)

      if auth_id:
        auth = True
        print "Host '" + auth_email + "' authenticated."

    else:
      print "Authentication failed."

    return auth

  # obsluga web service'ow
  def _dispatch(self, service, vars):    
    self.cookies = []        
    auth = self.authenticate_client() 

    if not auth:
      return "Authentication failed."

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
  print " Prosty serwer XML-RPC udostepniajacy przykladowe web services, ktore sa wywolywane w\n"
  print " requestach od klientow. Zanim serwer obsluzy jakiegokolwiek klienta musi go autoryzowac, a gdy\n"
  print " klient nie ma uprawnien to zostane odrzucony. Serwer ustawia cookies'y po stronie klienta,\n"
  print " zapisujac tym samym dane klienta w celu ulatwienia dalszych autoryzacji.\n"
  print " Web Services:\n"
  print " 'add(v1, v2)' - dodawanie\n"
  print " 'minus(v1, v2)' - odejmowanie\n"
  print " 'println(v)' - zwracanie stringa\n"
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
