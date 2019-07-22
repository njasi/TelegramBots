'''
This is a telegram bot that i use to setup for other telegram bots
it's mainly used to find a specific chat's id
'''

import json 
from requests import get
from time import sleep
import urllib

file = open("token.txt")
TOKEN = file.read().strip()
file.close()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

#
# Code dealing with sending and reciving messages
#

def get_url(url):
    response = get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)    

def main():
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            for update in updates["result"]:
                process(update)
            respond(updates)
        sleep(0.5)

def process(updates):
    # print(update)
    # print(update["message"]["from"])         # see who a message is from
    # print(update["message"]["chat"]["id"])   # find out the id of a chat

if __name__ == "__main__":
    main()