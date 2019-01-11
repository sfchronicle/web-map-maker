from poster.encode import multipart_encode
import SimpleHTTPServer
from ftplib import FTP
import urllib, urllib2
import SocketServer
import urlparse
import json
import os
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

            # Grab vars for FTP uploading
            with open('.env', 'r') as f:
                env_vars = json.load(f)

            

            # Grab data out of the post req
            content_len = int(self.headers.getheader('content-length', 0))
            post_body = self.rfile.read(content_len)
            fields = urlparse.parse_qs(post_body)
            pure_image = fields['image'][0].split(',', 1)[1]
            file_name = fields['slug'][0]+".png"

            # Write image to disk from data
            with open(file_name, "wb") as fh:
                fh.write(pure_image.decode('base64'))

            # my_file = {
            #   'file': (file_name, open(file_name, 'rb'), 'png')
            # }

            

            # r = requests.post("https://slack.com/api/files.upload", params=payload, files=my_file)
            print "HI"
            with open(file_name, 'rb') as uploadfile:
                payload = urllib.urlencode({
                    "token": env_vars["slack_bot_token"],
                    "filename": "composed_" + file_name,
                    "title": "Composed File",
                    "channels": ["CC571F06P"],
                    "file": uploadfile.read()
                })
                request = urllib2.Request("https://slack.com/api/files.upload", data=payload)
                response = urllib2.urlopen(request)
                print response.read()
            # WORKING -- THIS ALMOST WORKS


            # Init FTP session
            session = FTP(env_vars['ftp_server'],env_vars['ftp_username'],env_vars['ftp_password'])

            # Special handling for FTP system
            file = open(file_name,'rb')
            session.storbinary('STOR '+file_name, file)
            file.close()    
            session.quit()

            # Remove the file
            os.remove(file_name)

            # If we made it here, send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            return
      



httpd = SocketServer.ThreadingTCPServer(('', PORT),CustomHandler)
print("serving custom server at port ", PORT)
httpd.serve_forever()