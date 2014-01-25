#!/usr/bin/env python2.6

#################################################################
#                                                               #
#   XML-RPC Client                                              #
#   Projekt zaliczeniowy z Pracowni Jezykow Skryptowych         #
#   Uniwersytet Jagiellonski, Krakow                            #
#                                                               #
#   Klient wywolan XML-RPC                                      #
#   (c) 2014 Marcin Radlak                                      #
#   marcin.radlak@uj.edu.pl                                     #
#   http://marcinradlak.pl                                      #
#                                                               #
#################################################################

import getopt
import sys
import os
import base64
import xmlrpclib
import urllib2
import cookielib

class CookieResponse:
  def __init__(self, headers):
    self.headers = headers

  def info(self):
    return self.headers

class CookieClientTransporter(xmlrpclib.Transport):
  user_agent = '*py*'
  credentials = ()
  cookiefile = 'cookies.lwp'
        
  # informowanie o autoryzacji
  def send_basic_auth(self, connection):    
    auth = base64.encodestring("%s:%s"%self.credentials).strip()
    auth = 'Basic %s' %(auth,)
    connection.putheader('Authorization',auth)

  # pobieranie danych z cookies'ow
  def send_cookie_auth(self, connection):
    cj = cookielib.LWPCookieJar()
    cj.load(self.cookiefile)

    for cookie in cj:
      if cookie.name == 'ID':
        uuidstr = cookie.value

      connection.putheader(cookie.name, cookie.value)

  def send_host(self, connection, host):
    xmlrpclib.Transport.send_host(self, connection, host)

    if os.path.exists(self.cookiefile):
      self.send_cookie_auth(connection)

    elif self.credentials != ():
      self.send_basic_auth(connection)
                    
  def request(self, host, handler, request_body, verbose=0):
    crequest = urllib2.Request('http://'+host+'/')
            
    h = self.make_connection(host)

    if verbose:
      h.set_debuglevel(1)

    self.send_request(h, handler, request_body)
    self.send_host(h, host)
    self.send_user_agent(h)
        
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

def set_up_connection(serv, port, auth = ()):
  transporter = CookieClientTransporter()

  if auth!= ():
    transporter.credentials = auth

  uri = "http://" + serv + ":" + port
  client = xmlrpclib.Server(uri, transport=transporter, verbose=False)
    
  return client

def usage():
  print "-----------------------------------------------------------------------------------------------\n"
  print " XML-RPC Client\n\n"
  print " Uzycie: program [-s SERWER] [-p PORT] [-e EMAIL] [-n NAZWA] [--help|-h]\n\n"
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
    port = "8088"
    email = 'email@address.com'
    name = 'vaikings'

    for opt, val in opts:
      if opt in ("-h", "--help"):
        usage()
        sys.exit(0)
      elif opt == "-s":
        serv = val
      elif opt == "-p":
        port = val
      elif opt == "-e":
        email = val
      elif opt == "-n":
        name = val
    
    client = set_up_connection(serv, port, (email, name))

    print client.add(2, 2)
    print client.minus(4, 1)
    print client.println("Bla bla...")
    print client.ble()

  except getopt.GetoptError as err:
    print str(err)
    usage()
    sys.exit(1)
  except ValueError:
    usage()
    sys.exit(1)
  except Exception as err:
    print str(err)
    sys.exit(1)

# main
if __name__ == '__main__':
  main()
    