import SimpleHTTPServer
from ftplib import FTP
import SocketServer
import urlparse
import json
import re
PORT = 8000

class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        if None != re.search('/api/square/*', self.path):
            num = float(self.path.split('/')[-1])
            print self.path.split('/')
            #This URL will trigger our sample function and send what it returns back to the browser
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(str(num*num)) #call sample function here
            return
        if None != re.search('/api/mult/*', self.path):
            num1 = float(self.path.split('/')[-1])
            num2 = float(self.path.split('/')[-2])
            #This URL will trigger our sample function and send what it returns back to the browser
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(str(num1*num2)) #call sample function here
            return
        else:
            #serve files, and directory listings by following self.path from
            #current working directory
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)



    def do_POST(self):
        if ('/api/sendonline' == self.path):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            with open('.env', 'r') as f:
                env_vars = json.load(f)

            content_len = int(self.headers.getheader('content-length', 0))
            post_body = self.rfile.read(content_len)
            print env_vars


httpd = SocketServer.ThreadingTCPServer(('', PORT),CustomHandler)
print("serving custom server at port ", PORT)
httpd.serve_forever()