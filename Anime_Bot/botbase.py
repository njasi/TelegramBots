import urllib
import json
import string
from random import random
import requests

class BotBase:
    def __init__(self, token):
        self.TOKEN = token
        self.URL = "https://api.telegram.org/bot{}/".format(token)

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        response.close()
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = self.URL + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    def get_last_chat_id_and_text(self, updates):
        num_updates = len(updates["result"])
        last_update = num_updates - 1
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
        return (text, chat_id)

    def strip_punct(text):
        exclude=set(string.punctuation)
        return (''.join(ch for ch in text if ch not in exclude)).lower()

    def send_message(self, text, chat_id, parse_mode = "HTML", force_reply = None):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}&parse_mode={}".format(text, chat_id, parse_mode)
        if force_reply:
            boi = {"force_reply": True, "selective":True}
            url +="&reply_markup={}".format(urllib.parse.quote_plus(json.dumps(boi)))
        return self.get_json_from_url(url)

    def send_reply(self, text, chat_id, reply_to_id, force_reply = None):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}&reply_to_message_id={}".format(text, chat_id,reply_to_id)
        if force_reply:
            boi = {"force_reply": True}
            url +="&reply_markup={}".format(urllib.parse.quote_plus(json.dumps(boi)))
        self.get_url(url)

    def send_forward(self, message_id, from_id, to_id):
        url = self.URL + "forwardMessage?chat_id={}&from_chat_id={}&message_id={}".format(to_id,from_id,message_id)
        self.get_url(url)
        
    def delete_message(self, message_id, chat_id):
        url = self.URL + "deleteMessage?chat_id={}&message_id={}".format(chat_id,message_id)
        self.get_url(url)
    
    def send_reply_with_photo(self, caption, photo_url, chat_id, reply_to_id, force_reply = None):
        caption = text = urllib.parse.quote_plus(caption)
        url = self.URL + 'sendPhoto?photo={}&caption={}&chat_id={}&reply_to_message_id={}'.format(photo_url,caption,chat_id,reply_to_id)
        if force_reply:
            boi = {"force_reply": True, "selective":True}
            url += "&reply_markup={}".format(urllib.parse.quote_plus(json.dumps(boi)))
        self.get_url(url)

    def get_file(self, file_id):
        url = self.URL + "getFile?file_id={}".format(file_id)
        return self.get_json_from_url(url)