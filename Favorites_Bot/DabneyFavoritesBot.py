"""
With this bot you can store your favorite stickers all in one place! 
If you type in @DabneyFavoritesBot your favorite stickers will appear. 
If its not working try to include a space after the tag, so it 
should be "@DabneyFavoritesBot ". This is meant to be used as an 
extension to telegram's favorite sticker system which is 
capped at 5 stickers,
"""

import json, requests, time, urllib
from botbase import BotBase
from random import random

file = open("data/token.txt")
BOT = BotBase(file.read().strip())
file.close()
help_message = '<b>About:</b>\nWith this bot you can store your favorite stickers all in one place! If you type in @DabneyFavoritesBot your favorite stickers will appear. If its not working try to include a space after the tag, so it should be "@DabneyFavoritesBot "\n\n<b>Commands:</b>\n/addsticker: Add a sticker to your favorites.\n/removesticker: Remove a sticker from your favorites.\n/help: Get help...'
manage = {}

##################
# Helper Methods #
##################

def get_user_name(user):
    name = ''
    try:
        name = user["username"]
    except Exception:
        name = get_name(user)
    return name

def get_name(user):
    name = ''
    try:
        name += user["first_name"]
    except Exception as e:
        pass
    try:
        name += " " + user["last_name"]
    except Exception as e:
        pass
    return name

def is_thing(update,keys):
    try:
        test = update
        for key in keys:
            update = update[key]
    except Exception:
        return False
    return True

#####################################
# Stuff to manage favorite stickers #
#####################################

def register_check(user_id, people):
    if not user_id in people.keys():
        people[user_id] = ["0"]
    return people

def add_sticker(sticker_id, user_id):
    file = open("data/favorites.txt", "r")
    stickers = json.loads(file.readline().strip())
    people = json.loads(file.readline().strip())
    file.close()
    register_check(user_id, people)

    sticker_key = None
    if not sticker_id in stickers.values():
        keys = list(stickers.keys())
        sticker_key = len(keys)
        stickers[str(sticker_key)] = sticker_id
    else:
        for key in stickers:
            if stickers[key] == sticker_id:
                sticker_key = int(key)
                break
    if not str(sticker_key) in people[user_id]:
        people[user_id] += [str(sticker_key)]

    file = open("data/favorites.txt", "w")
    file.write(json.dumps(stickers)+"\n")
    file.write(json.dumps(people)+"\n")
    file.close()

def remove_sticker(sticker_id, user_id):
    file = open("data/favorites.txt")
    stickers = json.loads(file.readline().strip())
    people = json.loads(file.readline().strip())
    file.close()
    register_check(user_id, people)

    sticker_key = None
    if sticker_id in stickers.values():
        for key in stickers:
            if stickers[key] == sticker_id:
                sticker_key = key
                break
    else:
        return False
    people[user_id].remove(sticker_key)
    
    file = open("data/favorites.txt", "w")
    file.write(json.dumps(stickers)+"\n")
    file.write(json.dumps(people)+"\n")
    file.close()

def get_favorites(user_id):
    user_id = str(user_id)
    file = open("data/favorites.txt")
    stickers = json.loads(file.readline().strip())
    people = json.loads(file.readline().strip())
    register_check(user_id, people)
    out = []
    for key in people[user_id]:
        out += [stickers[key]]

    file.close()
    return out

def get_favorite_ids(user_id):
    user_id = str(user_id)
    file = open("data/favorites.txt")
    stickers = json.loads(file.readline().strip())
    people = json.loads(file.readline().strip())
    register_check(user_id, people)
    out = []
    for key in people[user_id]:
        out += [key]

    file.close()
    return out

def get_sticker_ids():
    file = open("data/favorites.txt")
    stickers = json.loads(file.readline().strip())
    file.close()
    return stickers

#####################
# Buttons and Stuff #
#####################

def send_options(chat_id, options, text, parse_mode = 'HTML', message_id = None):
    text = urllib.parse.quote_plus(text)
    keys = json.dumps(options)
    keys = urllib.parse.quote_plus(keys)
    url = BOT.URL + "sendMessage?text={}&chat_id={}&reply_markup={}&parse_mode={}".format(text,chat_id,keys,parse_mode)
    if message_id:
        url += "&reply_to_message_id={}".format(message_id)
    BOT.get_url(url)

def favorites_to_sticker_buttons(user_id):
    out = []
    stickers = get_sticker_ids()
    fav_ids = get_favorite_ids(user_id)
    for sticker in fav_ids:
        out += [{"type": "sticker", "id":str(sticker), "sticker_file_id":stickers[sticker]}]
    return out

def send_favorite_stickers(update):
    user_id = update["inline_query"]["from"]["id"]
    query_id = update["inline_query"]["id"]
    res = favorites_to_sticker_buttons(user_id)

    url = BOT.URL + "answerInlineQuery?inline_query_id={}".format(query_id)
    url += "&is_personal=TRUE"
    url += "&cache_time=0"
    switch_text = urllib.parse.quote_plus("Manage Your Stickers!")
    if len(res) == 0:
        switch_text = urllib.parse.quote_plus("Add Some Stickers Here!")

    url += "&switch_pm_text={}".format(switch_text)
    url += "&switch_pm_parameter=69"
    res = json.dumps(res)
    res = urllib.parse.quote_plus(res)
    url += "&results={}".format(res)        

    json_out = BOT.get_json_from_url(url)
    
###########################
# Bot response controller #
###########################

def respond(update):
    global manage

    if is_thing(update, ["inline_query"]):
        send_favorite_stickers(update)

    elif is_thing(update, ['callback_query']):
        data = update['callback_query']["data"]
        chat_id = update["callback_query"]["message"]["chat"]["id"]

    elif is_thing(update, ["message"]):
        chat_id = update["message"]["chat"]["id"]
        user_id = str(update["message"]["from"]["id"])
        message_id = update["message"]["message_id"]

        if is_thing(update, ['message', 'text']):
            text = update["message"]["text"]
            if "/help" in text or "/start" in text:
                BOT.send_message(help_message, chat_id)
            if "/addsticker" in text:
                manage[user_id] = "add"
                BOT.send_message("Please send the sticker you want to add!", chat_id)
            if "/removesticker" in text:
                manage[user_id] = "del"
                BOT.send_message("Please send the sticker you want to remove!", chat_id)
                
        elif is_thing(update, ["message","sticker"]):
            sticker_id = update["message"]["sticker"]["file_id"]
            if user_id in manage:
                stage = manage[user_id]
                if stage == "add":
                    add_sticker(sticker_id, user_id)
                    BOT.send_message("The sticker was added to your favorites!", chat_id)
                elif stage == "del":
                    remove_sticker(sticker_id, user_id)
                    BOT.send_message("The sticker was removed from your favorites!", chat_id)
                manage.pop(user_id)

##################
# Main Loop Shit #
##################

try_boi = True

def main():
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = BOT.get_last_update_id(updates) + 1
            for update in updates["result"]:
                if try_boi:
                    try:
                        respond(update)
                    except Exception as e:
                        BOT.send_message(str(e), "569239019")
                else:
                    respond(update)
        time.sleep(0.5)

if __name__ == '__main__':
    main()
