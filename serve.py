from ftplib import FTP
import urllib
import base64
import socketserver
import http.server
import requests
import json
import os
import re
PORT = 8000

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        #serve files, and directory listings by following self.path from
        #current working directory
        http.server.SimpleHTTPRequestHandler.do_GET(self)


    def do_POST(self):
        if ('/api/sendonline' == self.path):

            # Grab vars for FTP uploading
            with open('.env', 'r') as f:
                env_vars = json.load(f)

            # Grab data out of the post req
            content_len = int(self.headers.get('content-length', 0))
            post_body = self.rfile.read(content_len)
            fields = urllib.parse.parse_qs(post_body)

            # Convert byte data to strings
            newFields = {str(key, 'utf-8'): str(value[0], 'utf-8') for (key, value) in fields.items()}

            # Grab what we want
            pure_image = newFields['image'].split(',', 1)[1]
            file_name = newFields['slug']+".jpg"

            # Write image to disk from data
            imgdata = base64.b64decode(pure_image)
            with open(file_name, "wb") as fh:
                fh.write(imgdata)

            # Slack file prep
            my_file = {
              'file': (file_name, open(file_name, 'rb'), 'jpg')
            }
            payload={
              "filename": "map.jpg", 
              "token": env_vars["slack_bot_token"], 
              "channels": ["CC571F06P"], 
            }

            # Hit Slack with the image
            r = requests.post("https://slack.com/api/files.upload", params=payload, files=my_file)

            # Init FTP session
            session = FTP(env_vars['ftp_server'],env_vars['ftp_username'],env_vars['ftp_password'])
            # THIS WON'T WORK UNLESS THE DNS IS CORRECT
            # MAKE SURE /etc/resolv.conf IN EC2 HAS nameserver 10.212.32.227 AND nameserver 10.212.32.228 listed

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
      
with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print("serving custom server at port ", PORT)
    httpd.serve_forever()