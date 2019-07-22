import urllib
import json
import requests
from random import random

class BotBase:
    def __init__(self, url):
        self.URL = url

    def get_url(url):
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
        exclude.add('’')
        return (''.join(ch for ch in text if ch not in exclude)).lower()

    def send_message(self, text, chat_id):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
        self.get_url(url)

    def send_reply(self, text, chat_id, reply_to_id):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}&reply_to_message_id={}".format(text, chat_id,reply_to_id)
        self.get_url(url)
    
    def send_reply_with_photo(self, caption, photo_url, chat_id, reply_to_id):
        caption = text = urllib.parse.quote_plus(caption)
        url = self.URL + 'sendPhoto?photo={}&caption={}&chat_id={}&reply_to_message_id={}'.format(photo_url,caption,chat_id,reply_to_id)
        self.get_url(url)


    def respond_trigger_words(self, update, tokenize, triggers, responses):
        text = self.strip_punct(update["message"]["text"])
        if tokenize:
            text=text.split()
        chat = update["message"]["chat"]["id"]
        b = True
        for ands in triggers:
            a = False
            for ors in ands:
                if tokenize:
                    a = a or ors in text
                else:
                        a = a or text.find(ors)!=-1
            b = b and a
        if b:
            self.send_message(responses[random.randint(0,len(responses)-1)],chat)
            raise Exception('a response was triggered')
            
    def respond_trigger_words_user(self, update, tokenize, triggers, responses, userid):
        text = self.strip_punct(update["message"]["text"])
        if tokenize:
            text = text.split()
        chat = update["message"]["chat"]["id"]
        b = True
        for ands in triggers:
            a = False
            for ors in ands:
                if tokenize:
                    a = a or ors in text
                else:
                    a = a or text.find(ors)!=-1
            b = b and a
        if b:
            try:
                self.send_message(responses[userid.index(update["message"]["from"]["id"])+1],chat)
            except Exception as e:
                self.send_message(responses[0],chat)
                raise Exception('a response was triggered')