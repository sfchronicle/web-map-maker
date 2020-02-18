from ftplib import FTP
import urllib
import base64
import socketserver
import http.server
import requests
import json
import os
import re
import slack
import subprocess
import configparser
import random
PORT = 8000

# Parse the config 
cp = configparser.ConfigParser(interpolation=None)
cp.read(".env")

# Prep slack
app_slack_token = cp.get('slack', 'slack_app_token')
app_sc = slack.WebClient(app_slack_token)
bot_slack_token = cp.get('slack', 'slack_bot_token')
bot_sc = slack.WebClient(bot_slack_token)
deploy_feed = "CC571F06P"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print("GET");

        if ('/enter' == self.path):
            # Special command for the enter key
            print("ENTER DETECTED")
            # Ask Slack for latest message from deploy channel
            slack_resp = requests.get("https://slack.com/api/conversations.history?token="+app_slack_token+"&channel=GGCTB5UQ5&count=1")
            slack_data = slack_resp.json()
            try:
                # Check for the button
                first_message = slack_data['messages'][0]
                if 'live' in first_message['attachments'][0]['actions'][0]['value']:

                    # Fire off req to allow the deploy
                    aws_resp = requests.get("https://projects.sfchronicle.com/feeds/slack-endpoint/allow.php?key=deYoung901&file="+first_message['attachments'][0]['actions'][0]['value'])

                    if (aws_resp.status_code == 200):
                        # If we're successful, change the Slack message
                        payload = {
                            'token': app_slack_token, 
                            'channel': 'GGCTB5UQ5',
                            'text': first_message['text'] + "\n*PROJECT DEPLOYED BY SMASHING THE ENTER BUTTON*",
                            'ts': first_message['ts'],
                            'attachments': [{"pretext": "DEPLOYED", "text": "*PROJECT DEPLOYED BY SMASHING THE ENTER BUTTON*"}]
                        }
                        update_resp = requests.post("https://slack.com/api/chat.update", data=payload)
                    
                else:
                    raise ValueError('Not what we are looking for')
            except Exception as e:
                # DO NOTHING
                print("deploy button is not in most recent message")

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
        else:    
            #serve files, and directory listings by following self.path from
            #current working directory
            http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):

        if ('/log' == self.path):

            output = subprocess.check_output("docker-compose logs --tail=\"200\"", shell=True, cwd="/home/ec2-user/Projects/deploy-engine")
            output = output.decode("utf-8")

            app_sc.files_upload(
                filename=random.choice(["This is why the deploy broke", "Don't be sad, here's a log for you", "Success is just one deploy away", "Knowledge is power", "Accidentally a thing", "If at first you don't succeed...", "Have you tried turning it off and on again?"]),
                channels=deploy_feed,
                filetype="shell",
                content=output
            )

            # If we made it here, send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            return


        if ('/api/sendonline' == self.path):

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
            # THIS ISNT WORKING BUT USED TO
            # app_sc.files_upload(
            #     filename="Mapmaker Map",
            #     channels=[deploy_feed],
            #     file=imgdata
            # )
         
            # Init FTP session
            session = FTP(cp.get('ftp', 'ftp_server'),cp.get('ftp', 'ftp_username'),cp.get('ftp', 'ftp_password'))
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