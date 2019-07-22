#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This is a telegram bot paired with a rasberry pi which has a camera.
It can detect motion and sends a message to the OATS chat with an 
image when it detects any motion. The area(s) of interest will be 
boxed in a green outline.

    - users can request to see the feed with /view
    - just for fun there is a leaderboard to keep 
      track of who uses it the most.

This bot is called "Oats Viewer" because it watchs a bowl of oats
in the dabney courtyard which always attracts squirrels.

- This is adapted from a motion dector I made for dabney's interhouse party.
"""

from picamera import PiCamera
from picamera.array import PiRGBArray
from time import sleep
from datetime import datetime
import imutils
import cv2
import botbase
import json 
import requests
import threading
from PIL import ImageFont, ImageDraw, Image  


CAMERA_RES =(1920, 1088)
view_info = (False, 0, 0)
file = open("token.txt")
TOKEN = file.read().strip()
file.close()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
BOT = botbase.BotBase(URL)

def view_leaderboard(start = 0):
    lead = open("leaderboard.txt","r")
    line = lead.readline()
    stats = json.loads(line)
    lead.close()
    sorted = []
    for key in stats:
        if str(key) == "650557855":
            stats[key][0] = 68
        sorted += [(stats[key][0], stats[key][1], key)]
    sorted.sort()
    sorted.reverse()
    i = 0
    returner = "<b>O A T S   Leaderboard:</b>\n"
    for user in sorted:
        count = user[0]
        if(i > len(sorted) or i - start > 9):
            break
        if(user[2]== "569239019"):
            count = "m̵̯͈̚͝ä̶̬͉́n̸̲̑̔y̸̤̯̍"
        if (i >= start - 1):
            returner += "<b>{}</b>:\t{} has viewed {} O A T S!\n".format(i + 1, user[1], count)
        i+=1
    if returner == "<b>O A T S   Leaderboard:</b>\n":
        return "I N V A L I D   S T A R T   A R G U M E N T"
    return returner.replace("/n","<br>")
    
def update_leaderboard(user_id, name):
    lead = open("leaderboard.txt","r")
    stats = json.loads(lead.readline())
    lead.close()
    try:
        stats[str(user_id)][0] += 1
    except KeyError as e:
        stats[str(user_id)] = (1, name)
    lead = open("leaderboard.txt","w")
    lead.write(json.dumps(stats))
    lead.close()  

def unview(target, amount):
    lead = open("leaderboard.txt","r")
    stats = json.loads(lead.readline())
    lead.close()
    for key in stats: 
        if stats[key][1] == target:
            stats[key][0] -= amount
            break
    lead = open("leaderboard.txt","w")
    lead.write(json.dumps(stats))
    lead.close()  

def send_photo_from_file(chat_id,filename, caption = "URGENT! THERE WAS MOTION DETECTED NEAR THE OATS", reply = False, reply_id = 0):
    file = open(filename, 'rb')
    files = {'photo':file}
    now = datetime.now()
    if reply:
        status = requests.post('https://api.telegram.org/bot{}/sendPhoto?chat_id={}&caption={}&reply_to_message_id={}'.format(TOKEN, chat_id, caption, reply_id), files=files)
    else:
        status = requests.post('https://api.telegram.org/bot{}/sendPhoto?chat_id={}&caption={}'.format(TOKEN, chat_id, caption), files=files)
    file.close()

def detect_and_send():
    global view_info
    MIN_AREA = 100
    BLUR_SIZE = (21,21)

    # initialize the camera and grab a reference to the raw camera capture
    camera = PiCamera()
    camera.resolution = CAMERA_RES
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=CAMERA_RES)
    firstFrame = None
    # loop over the frames of the video
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the current frame
        text = "O A T S   C A M   H I G H   D E F I N I T I O N   T M"
        image = frame.array
        motion = False
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, BLUR_SIZE, 0)

        if firstFrame is None:
            firstFrame = gray
        frameDelta = cv2.absdiff(firstFrame, gray)

        thresh = cv2.threshold(frameDelta, 25, 0xFF, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        cv2.rectangle(thresh, (0, 0), (183, 560), (0, 0xFF, 0), cv2.FILLED)
        cv2.rectangle(thresh, CAMERA_RES, (1520, 600), (0, 0xFF, 0), cv2.FILLED)
        
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        firstFrame = gray
        for c in cnts:
            if cv2.contourArea(c) < MIN_AREA:
                continue

            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0xFF, 0), 2)
            motion = True
            text = "H I G H   D E F I N I T I O N   O A T S   M O T I O N   D E T E C T E D"

        cv2.putText(image,text,(10, 20),cv2.FONT_HERSHEY_SIMPLEX,
                0.5,(0, 0, 0xFF),2,)
        cv2.putText(image,datetime.now().strftime('%A %d %B %Y %I:%M:%S%p'),
        (10, image.shape[0] - 10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0, 0, 0xFF),1,)
        if view_info[0] and not motion:
            cv2.imwrite("security.png",image)
            send_photo_from_file(view_info[1], "security.png", caption = "Live view of oats!", reply = True, reply_id = view_info[2])
            view_info = (False , 0, 0)
        if motion:
            cv2.imwrite("security.png",image)
            send_photo_from_file(-1001463557977, "security.png") #-1001463557977 is the Oats chat_id
        else: 
            #BOT.send_message("no motion", 569239019)
            pass
        rawCapture.truncate(0)

def main():
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = BOT.get_last_update_id(updates) + 1
            respond(updates)
        sleep(0.5)

def respond(updates):
    for update in updates["result"]:
        try:
            do_commands(update)
        except Exception as e:
            #print(e)
            pass

def do_commands(update):
    global view_info
    text = update["message"]["text"]
    if "/view" in text: 
        last_name = ''
        try:
            last_name = " " + update["message"]["from"]["last_name"]
        except:
            pass
        view_info = (True, update["message"]["chat"]["id"], update["message"]["message_id"])
        update_leaderboard(update["message"]["from"]["id"], update["message"]["from"]["first_name"] + last_name)  
    elif '/leaderboard' in text:
        starter = 0
        try:
            starter = int(text.replace('/leaderboard','').replace("@_oats_viewer_bot",'').strip())
        except:
            starter = 0
        BOT.send_reply(view_leaderboard(start = starter),update["message"]["chat"]["id"],update["message"]["message_id"], parse_mode = "HTML")
    elif '/unview' in text:
        if str(update["message"]["from"]["id"]) == "569239019":
            args = text.replace("/unview ","").split(" ")
            target =""
            amount = 0
            if len(args) == 3:
                target = args[0] + " " + args[1]
                amount = args[2]
            elif len(args) == 2:
                target = args[0]
                amount = args[1]
            if target == "":
                BOT.send_reply("I N V A L I D   A R G U M E N T S", update["message"]["chat"]["id"],update["message"]["message_id"])
            else:
                unview(target, int(amount))
        else:
            BOT.send_reply("O N L Y   T H E   O A T S   M A S T E R   C A N    U N V I E W   O A T S", update["message"]["chat"]["id"],update["message"]["message_id"])

if __name__ == '__main__':
    one = threading.Thread(target=detect_and_send, args=())
    one.start()

    two = threading.Thread(target=main, args=())
    two.start()