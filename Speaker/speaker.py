"""
This is a telegram bot that reads the messages of all chats
that it is in out loud to me with the use of gtts
"""

from time import sleep
from os import system
from gtts import gTTS
import botbase

QUIT = False
file = open("token.txt")
TOKEN = file.read().strip()
file.close()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
BOT = botbase.BotBase(URL)

def main():
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = BOT.get_last_update_id(updates) + 1
            read(updates)
        sleep(0.5)

def read(updates):
    for update in updates["result"]:
        try:
            dm = not ((update['message']['chat']['id'] is not None) and update['message']['chat']['id'] == update['message']['from']['id'])
            message = update['message']
            name = message['from']['first_name']
            text = message['text']
            if not dm:
                BOT.send_message("Your message will play soon!", update['message']['from']['id'])
            BOT.send_message("{} said: {}".format(name,text),569239019)
            speak("{} said: {}".format(name,text))
            if not dm:
                BOT.send_message("Your message was played: \n{}".format(text), update['message']['from']['id'])
        except Exception as e:
            # raise(e)
            pass

def speak(toread):
    myobj = gTTS(text = toread, lang='en', slow=False)
    myobj.save("toplay.mp3") 
    os.system("afplay toplay.mp3") 

if __name__ == '__main__':
    main()  