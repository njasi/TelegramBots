'''
This is a bot that is made for people in my house (dorm) to confess anything anonmously.
This sometimes gets used to aks questions one is too embarassed to ask and similar situations.
Features:
    - You can message it text, stickers, audio, photos, 
      documents,video, voice, and animations(gifs)
    - Provides an optional time delay on your message 
      (10-15 min, 30-45 min, 1-2hr, and instant)
      at this stage there is also a cancel option
    - After the time delay is finished the bot will send out 
      your confession to two chats, one where people can discuss
      and the other for people to just view the confessions
    - if a confessor desires they can make the bot reply 
      to another confession by typing @#<confession number>
      at the start of their confession.
    - /feedback sends anon feedback to the creator
    - /lock allows you to lock the bot so it wont 
      try to confess your messages (this is a special request)
    - /help gives help

Other info:
    - At the time of this release (7/22/19) the bot has processed over 2,665 confessions
      (no way to know how many confessions have been canceled)
    - This is not moderated but there is a general no 18+ rule.
'''

import json 
import time
import urllib
from botbase_small import BotBase
from random import random

reader = open('data/token.txt','r')
TOKEN = reader.readline()
reader.close()
waiting = []
feedback = []
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
BOT = BotBase(URL)
confession_messages = ['Thank you for your sins.','...','[insert appropriate response here]',"Confess me harder daddy","How does that make you feel?","According to all know laws of aviation, there is no way the bee should be able to fly.","MÌÌÌÍ¯ÌÌÌuÍÌ«ÍdÌ¼Ì±Ì­ÌÌá£Ì°ÌÌÍÌ³Í®ÍÍuÌ¸ÍÌÍÌÌ®ÌÌ½Í¦ÌÌtÌ©ÌÍ¥ÌÍ®Í©sÌ«ÌºÌ¹ÌÌ»Ì±ÌÌÍ¬ÍªÍ«ÌÌÌ ÍÌ­ÌÌ½ÌÌÌÍ¨Í¥Ã¬Ì Ì®Ì«ÍsÌªÌ³Ì³Ì³Ì»ÌÌ£Í Ì¤ÍÌÍªÍ¤ÌtÌ°ÌÍÌ¦Ì»Ì¼Í¥ÍÍ¤ÍhÌ¤Ì¤eÌ¿Í¥Ì¿ÌÌÍ¡ Ì¬Ì¤Ì¼ÍÌ¿ÌÌÌÍÍ¢bÍÍÍÍÌ¯ÍÌÌÌÌÌÌÌeÌÌÌ¬ÌÌÍÌÍÌ¾ÌÌsÍÌ¤ÍÍÌÌÍÌÍ¤ÍÍÍÈÍÍÌ­Ì¼Ì¤Ì¯ÌÌÌÍ¦ÍÍ ÌÍÍ¯ÍÌÌ¿ÌÈÌ´ÌÌ©Ì²ÍÍÌ³Ì¹Í¥Í©fÍÌ¬Ì°ÌÌÌÌÍ¬Ì½Í¥ ÍÌ¹Ì®ÍÌÃ¢Ì»ÌÌ¯ÍÍÌ¯Ì¾ÍlÌ¥ÌÍ«ÌÌÌÌÌlÍ¨ÌÌÌ¾ÌÍÍ¢ ÌÌ³Ì£Ì­ÍÌ²ÌÍ¦ÌÌ¿pÌªÌÍÍ¬ÍoÍÌ¾ÌÌÌÌÅ¡ÍÍ¤Ì½Ì¿ÍsÍÌ°ÌºÌ¤ÌÌ½ÌÌ¾ÍiÍÌºÍÌªÌºÌ»ÌbÍÌ¼ÍÌ½Í¨ÌÍ¢lÍ¯ÍÍÄÌ Ì¹Ì¯ÍªÌÍ«Í­Í Í¤ÌÍ¨ÌpÌÍÌÍÌÍÍ«Ã Ì«ÌÍÌrÌ®Ì®ÍÌ¦ÌÌÌÍÌ½ÍÌÍªÍ­ÍÍtÌ¸Ì³Ì¦ÌªÌ­Ì¼ÍÌ®ÌÍ¯ÍÌÌÌÌÌyÌÌ¬ÍÌÌ Ì¤ÍÌÌtÍÌ¤ÍÌªÌ³ÍÌ¿ÌÌÌÌÍÍhÌ·ÍÍÌÌ½eÍmÌ¬ÍÌÌ³Ì®ÌeÍ®ÍÌÍ«ÌÍsÌºÌÌ«ÍÍÍ¦"]
help_message = "<b>Commands:</b> \n/feedback - Send anon feedback to the creator (@njasi).\n/poll - Send an anon poll to the confessions chats.\n/help - ...\n<b>To send a confession:</b>\nJust send a message here and then Confessions Bot wil give you time delay options (and a cancel option). Confessions Bot currently supports Text, Stickers, Images, Videos, Audio, Documents, Gifs and Voice. Polls are coming soon!"

def load_chats():
    holder = []
    reader = open('data/chats.txt')
    for line in reader.readlines():
        holder += [int(line.strip())]
    reader.close()
    return holder

chats = load_chats()

def should_message_be_sent(update):
    try:
        return ((update['message']['chat']['id'] is not None) and update['message']['chat']['id'] == update['message']['from']['id']) and update['message']['text'] != '/start'
    except:
        return True

def send_time_options(chat_id,message_id):
    text = urllib.parse.quote_plus('How long from now would you like your message to be sent?')
    keys = json.dumps({'inline_keyboard': [[{'text' : 'Instant', 'callback_data':3},{'text' : 'Cancel', 'callback_data':4}],[{'text' : '10 - 15 mins', 'callback_data':0},{'text' : '30 - 45 mins', 'callback_data':1},{'text' : '1 - 2 hrs', 'callback_data':2}]]})
    keys = urllib.parse.quote_plus(keys)
    url = URL + "sendMessage?text={}&chat_id={}&reply_markup={}&reply_to_message_id={}".format(text,chat_id,keys,message_id)
    BOT.get_url(url)

def url_message_from_data(data):
    type = data['type']
    number = get_confession_number() + 1
    update_confession_number(number)
    if(type == 'text'):

        text = urllib.parse.quote_plus('Confession #{}:\n'.format(number) + data['text'])
        return (URL + 'sendMessage?text={}'.format(text), reply_from_text(text))

    elif(type == 'sticker'):
        update_confession_number(number - 1)
        return URL + 'sendSticker?sticker={}'.format(data['file_id'])

    elif(type == 'photo'):
        caption = 'Confession #{}:\n'.format(number) + data['caption']
        caption = urllib.parse.quote_plus(caption)
        return (URL + 'sendPhoto?photo={}&caption={}'.format(data['file_id'],caption), reply_from_text(caption))

    elif(type == 'audio'):
        caption = 'Confession #{}:\n'.format(number) + data['caption']
        caption = urllib.parse.quote_plus(caption)
        return (URL + 'sendAudio?audio={}&caption={}'.format(data['file_id'],caption), reply_from_text(caption))

    elif(type == 'document'):
        caption = 'Confession #{}:\n'.format(number) + data['caption']
        caption = urllib.parse.quote_plus(caption)
        return (URL + 'sendDocument?document={}&caption={}'.format(data['file_id'],caption), reply_from_text(caption))

    elif(type == 'video'):
        caption = 'Confession #{}:\n'.format(number) + data['caption']
        caption = urllib.parse.quote_plus(caption)
        return (URL + 'sendVideo?video={}&caption={}'.format(data['file_id'],caption), reply_from_text(caption))

    elif(type == 'animation'):
        caption = 'Confession #{}:\n'.format(number) + data['caption']
        caption = urllib.parse.quote_plus(caption)
        return (URL + 'sendAnimation?animation={}&caption={}'.format(data['file_id'],caption), reply_from_text(caption))

    elif(type == 'voice'):
        caption = 'Confession #{}:\n'.format(number) + data['caption']
        caption = urllib.parse.quote_plus(caption)
        return (URL + 'sendVoice?voice={}&caption={}'.format(data['file_id'],caption), reply_from_text(caption))

    elif(type == 'poll'):
        question = 'Confession #{}:\n'.format(number) + data['question']
        if len(question) > 255:
            question = question[0:255]
        question = urllib.parse.quote_plus(caption)
        options = data["options"]
        return URL + 'sendPoll?question={}&options={}'.format(question, options)

def data_from_update(update):
    data = {}
    if not should_message_be_sent(update):
        return None

    try: #  poll
        poll = text = update['message']['poll']
    except:
        pass
    
    try: # normal text message
        text = update['message']['text']
        data['type'] = 'text'
        data['text'] = text
        return data
    except Exception:
        pass
        
    try: # stickers 
        file_id = update['message']['sticker']['file_id']
        data['type'] = 'sticker'
        data['file_id'] = file_id
        return data
    except Exception:
        pass

    try: # captions for documents and such
        caption = update['message']['caption']
    except Exception:
        caption = ''
    
    data['caption'] = caption # all of the types after this have captions

    try: # photo
        sizes = update['message']['photo']
        file_id = update['message']['photo'][len(sizes)-1]['file_id']
        data['type'] = 'photo'
        data['file_id'] = file_id
        return data
    except Exception as e:
        pass
        
    try: # audio
        file_id = update['message']['audio']['file_id']
        data['type'] = 'audio'
        data['file_id'] = file_id
        return data
    except Exception:
        pass
        
    try: # document
        file_id = update['message']['document']['file_id']
        data['type'] = 'document'
        data['file_id'] = file_id
        return data
    except Exception:
        pass

    try: # video
        file_id = update['message']['video']['file_id']
        data['type'] = 'video'
        data['file_id'] = file_id
        return data
    except Exception:
        pass

    try: # animation
        file_id = update['message']['animation']['file_id']
        data['type'] = 'animation'
        data['file_id'] = file_id
        return data
    except Exception:
        pass

    try: # voice
        file_id = update['message']['voice']['file_id']
        data['type'] = 'voice'
        data['file_id'] = file_id
        return data
    except Exception:
        pass

    return None # to detect that a message that is not sendable was recived
     
def update_confession_number(number):
    num = open('data/num.txt','w+')
    num.write(str(number))
    num.close()

def get_confession_number():
    num = open('data/num.txt','r')
    hold = int(num.readline())
    num.close()
    return hold

def reply_from_text(text):
    if text.find("%40%23") > -1:
        nums = "1234567890"
        num = ""
        index = text.find("%40%23")
        after = text[index + 6:len(text)]
        for character in after:
            if character not in nums:
                break
            num += character
        result_main = get_reply_id(num,"data/reply_info_main.txt")
        result_channel = get_reply_id(num,"data/reply_info_channel.txt")
        result_test = get_reply_id(num,"data/reply_info_test.txt")
        re = "&reply_to_message_id={}"
        return (re.format(result_main), re.format(result_channel), re.format(result_test))
    return ("","","")

def get_reply_id(c_num,file):
    boi = open(file)
    ids = json.loads(boi.readline())
    boi.close()
    try:
        return ids[c_num]
    except Exception as e:
        return ""

def add_reply_id(c_num, message_id, file_path):
    file = open(file_path, "r")
    data = json.loads(file.readline())
    data[str(c_num)] = int(message_id)
    file.close()
    file = open(file_path, "w")
    file.write(json.dumps(data))
    file.close()
    
def is_command(command_name, update):
    try:
        return "/{}".format(command_name) in update["message"]["text"]
    except:
        pass
    return False

def main():
    global waiting
    waiting = []
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = BOT.get_last_update_id(updates) + 1
            add_to_buffer(updates['result'])
            respond()
        time.sleep(0.5)

def add_feed_wait(update):
    global feedback
    feedback += [update["message"]["from"]["id"]]

def is_feedback(update):
    try:
        return update["message"]["chat"]["id"] in feedback and update["message"]["chat"]["id"] == update["message"]["from"]["id"]
    except:
        pass
    return False

def add_to_buffer(updates):
    global waiting
    global feedback
    for update in updates:
        try:
            if is_feedback(update):
                file = open("data/feedback.txt","a")
                file.write("{}\n\n".format(update["message"]["text"]))
                file.close()
                feedback.remove(update["message"]["from"]["id"])
                BOT.send_message("Thank you for the feedback!", update["message"]["from"]["id"])
                continue
            elif is_button_response(update):
                check_waiting(update['callback_query'])
            elif is_command("help", update):
                BOT.send_message(help_message, update["message"]["from"]["id"])
                continue
            elif is_command("poll", update):
                pass
            elif is_command("lock", update):
                add_locked(update["message"]["from"]["id"])
                BOT.send_message("Confessions Bot has been locked for you. It will no longer read any of your messages. use /unlock to undo this", update["message"]["from"]["id"])
            elif is_command("unlock", update):
                remove_locked(update["message"]["from"]["id"])
                BOT.send_message("Confessions Bot has been unlocked for you. It will now read your messages. use /lock to lock confessions bot this", update["message"]["from"]["id"])
                continue
            elif is_command("feedback", update):
                add_feed_wait(update)
                BOT.send_message("Ok please send your feedback!", update["message"]["from"]["id"])
                continue
            if is_locked(update["message"]["from"]["id"]):
                continue
            data = {}
            data['data'] = data_from_update(update)

            if data['data'] is not None:
                data['id'] = update['message']['message_id']  # only stored temporarliy while the bot waits for a time option
                data['from'] = update['message']['from']['id']
                data['data'] = json.dumps(data['data'])
                send_time_options(update['message']['from']['id'],update['message']['message_id'])
                waiting += [data]
        except Exception as e:
            if not str(e) == 'added_message':
                #raise(e)
                send_error(e,update)
                returner = False
            
def check_waiting(query):
    global waiting
    for message in waiting:
        if query['from']['id'] == message['from'] and message['id'] == query['message']['reply_to_message']['message_id']:
            waiting.remove(message)
            messages = open('data/messages.txt','a')
            data = {}
            if(query['data'] == '0'):
                data['send_time'] = int(random() * 300) + 600   # 10 - 15 min
            elif query['data'] == '1':
                data['send_time'] = int(random() * 900) + 1800  # 30 - 45 min
            elif query['data'] == '2':
                data['send_time'] = int(random() * 3600) + 3600 # 1 - 2 hrs
            elif query['data'] == '3':
                data['send_time'] = 0                           # Instant
            elif query['data'] == '4':
                BOT.send_message('Okay, your confession was canceled.', message['from'])
                return   
            data['data'] = message['data']
            data['send_time'] += int(time.time())
            messages.write(json.dumps(data) + '\n') 
            messages.close()
            BOT.send_message(confession_messages[int(random() * len(confession_messages))],message['from'])

def is_button_response(update):
    try:
        update['callback_query']
    except Exception:
        return False
    return True
    
def send_error(e,update):
    try:
        BOT.send_message('Dabney Confessions was unable to process your message.\nError message: ' + str(e), update['message']['from']['id'])
        BOT.send_message('/bigoofletjaSINskiknow', update['message']['from']['id'])
    except:
        pass

def add_locked(id):
    id = int(id)
    file = open("data//locked.txt", "r")
    data = json.loads(file.readline().strip())
    file.close()
    if not id in data:
        data += [id]
    file = open("data//locked.txt", "w")
    file.write(json.dumps(data))
    file.close()

def remove_locked(id):
    id = int(id)
    file = open("data//locked.txt", "r")
    data = json.loads(file.readline().strip())
    file.close()
    if id in data:
        data.remove(id)
    file = open("data//locked.txt", "w")
    file.write(json.dumps(data))
    file.close()

def is_locked(id):
    file = open("data//locked.txt", "r")
    data = json.loads(file.readline().strip())
    file.close()
    return int(id) in data

# -1001159774540 = main
# -1001312134444 = channel
def send_data(data):
    results = url_message_from_data(json.loads(data['data']))
    url = results[0]
    number = get_confession_number()
    for chat in chats:
        try:
            if not data['data'] is None:
                if int(chat) == -1001159774540: #main
                    message = BOT.get_json_from_url(url + results[1][0] + "&chat_id={}".format(chat))
                    add_reply_id(number,message["result"]["message_id"],"data/reply_info_main.txt")

                elif int(chat) == -1001312134444: #channel
                    message = BOT.get_json_from_url(url + results[1][1] + "&chat_id={}".format(chat))
                    add_reply_id(number,message["result"]["message_id"],"data/reply_info_channel.txt")

                else: #test_chat
                    message = BOT.get_json_from_url(url + results[1][2] + "&chat_id={}".format(chat))
                    add_reply_id(number,message["result"]["message_id"],"data/reply_info_test.txt")
        except Exception as e:
            pass

def respond():
    file = open('data/messages.txt','r')
    to_remove = []
    while True:
        line = file.readline()
        line = line.rstrip()
        if not line: break
        data = json.loads(line)
        if int(time.time()) > data['send_time']:
            send_data(data)
            to_remove += [data]
    file.close()
    file = open('data/messages.txt','r')
    old_lines = file.readlines()
    file.close()
    file = open('data/messages.txt','w')
    for line in old_lines:
        if not json.loads(line.strip()) in to_remove:
            file.write(line)

if __name__ == '__main__':
    main()


