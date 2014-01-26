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

import getopt, xmlrpclib, urllib2, sys, os, cookielib, base64

class Cookie:
  def __init__(self, content):
    self.content = content

  def info(self):
    return self.content

class CookieClientTransporter(xmlrpclib.Transport):
  email = ""
  password = ""
  new_user = None
  cookie_file = "cookie.lwp"
                    
  def request(self, host, handler, content, verbose = 0):
    uri = "http://" + host
    request = urllib2.Request(uri)
            
    conn = self.make_connection(host)

    if verbose:
      conn.set_debuglevel(1)
    self.verbose = verbose

    self.send_request(conn, handler, content)
    self.send_host(conn, host)
    self.send_user_agent(conn)                     
    self.send_content(conn, content)
            
    error, error_msg, headers = conn.getreply()

    cookie_jar = cookielib.LWPCookieJar()
    cookie_jar.extract_cookies(Cookie(headers), request)

    if len(cookie_jar) > 0 and self.cookie_file != None:
      cookie_jar.save(self.cookie_file)
                
    if error != 200:
      raise ProtocolError(host + handler, error, error_msg, headers)

    try:
      socket = conn._conn.sock
    except AttributeError:
      socket = None
                
    return self._parse_response(conn.getfile(), socket)

  def send_host(self, conn, host):
    xmlrpclib.Transport.send_host(self, conn, host)

    if ((self.email == "" or self.password == "") and not os.path.exists(self.cookie_file)) or ((self.email == "" or self.password == "") and self.new_user):
      print "Wrong email or password."
      sys.exit(1)

    # informowanie o autoryzacookie_jari
    if not os.path.exists(self.cookie_file):
      print "No cookie file."
      auth = "Data " + base64.encodestring(self.email + ":" + self.password).strip()

      if not self.new_user:
        conn.putheader('signin', auth)
      else:
        conn.putheader('register', auth)

    # pobieranie danych z cookies'ow
    else:
      cookie_jar = cookielib.LWPCookieJar()
      cookie_jar.load(self.cookie_file)

      for cookie in cookie_jar:
        conn.putheader(cookie.name, cookie.value)

def set_up_connection(serv, port, email, password, new_user):
  transporter = CookieClientTransporter()

  transporter.email = email
  transporter.password = password
  transporter.new_user = new_user

  uri = "http://" + serv + ":" + port
  client = xmlrpclib.Server(uri, transport=transporter, verbose=False)
    
  return client

def usage():
  print "-----------------------------------------------------------------------------------------------\n"
  print " XML-RPC Client\n\n"
  print " Uzycie: program [-s SERWER] [-p PORT] [-e EMAIL] [-n NAZWA] [-r] [--help|-h]\n\n"
  print " Prosty klient umozliwiajacy komunikacookie_jare z serwerem XML-RPC w celu wysylania requestow\n"
  print " z wywolaniami prostych metod.\n"
  print " Jak dziala:\n"
  print " 1. Przy probie pierwszego polaczenia z serwerem nalezy wczesniej zarejestrowac hosta, przy\n"
  print " uzyciu argumentu -r oraz padniu email'a i hasla. Serwer zarejestruje host i ustawi plik\n"
  print " cookie.\n"
  print " 2. Przy probie kolejnego polaczenia client bedzie pobieral dane uwierzytelniajace z pliku\n"
  print " cookie, jesli taki istnieje, z podaniem danych lub bez ich podania.\n"
  print " 3. Jesli plik cookie nie bedzie istnial, a host zostal zarejestrowany to serwer go utworzy.\n"
  print " 4. Plik cookie zostanie nadpisany w przypadku rejestracji nowego hosta. \n"
  print "-----------------------------------------------------------------------------------------------\n"

# glowna funkcookie_jara
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "rhs:p:e:n:", ["help"])

    serv = "localhost"
    port = "8088"
    email = ""
    name = ""
    new_user = None

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
      elif opt == "-r":
        new_user = True

    print email
    
    client = set_up_connection(serv, port, email, name, new_user)

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
    