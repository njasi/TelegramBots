import urllib
import json
import string
from random import random
import requests

class BotBase:
    def __init__(self, url):
        self.URL = url

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
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

    def send_message(self, text, chat_id):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
        self.get_url(url)
