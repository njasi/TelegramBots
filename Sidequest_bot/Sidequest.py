import json
import urllib
from botbase_small import BotBase
from time import sleep

file = open("data/token.txt")
TOKEN = file.read().strip()
file.close()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
BOT = BotBase(URL)
waiting = []
quest_chat = -1001339650768
help_message = '/viewquests:\nView all currently active sidequests.\n/myquests:\nView all of your active sidequests and remove old ones.\n/questcount:\nSee how many sidequests are currently active.\n/newquest:\nCreate a new sidequest!\n/help:\nGet help...'

YESORNO = {'inline_keyboard': [[{'text' : 'No', 'callback_data':0},{'text' : 'Yes', 'callback_data':1}],[{'text' : 'Cancel', 'callback_data':2}]]}

def gen_ACCEPT(data):
    return {'inline_keyboard': [[{'text' : 'Accept this sidequest?', 'callback_data':"a?" + str(data)}]]}

def gen_MINE(data):
    return {'inline_keyboard': [[{'text' : 'Remove this sidequest?', 'callback_data':"r?"+str(data)}],[{'text' : 'Poke the chat', 'callback_data': "p?"+ str(data)}]]}

def should_message_be_sent(update):
    try:
        return ((update['message']['chat']['id'] is not None) and update['message']['chat']['id'] == update['message']['from']['id']) and update['message']['text'] != '/start'
    except:
        return True

def send_options(chat_id, options, text, parse_mode = 'HTML', message_id = None):
    text = urllib.parse.quote_plus(text)
    keys = json.dumps(options)
    keys = urllib.parse.quote_plus(keys)
    url = URL + "sendMessage?text={}&chat_id={}&reply_markup={}&parse_mode={}".format(text,chat_id,keys,parse_mode)
    if message_id:
        url += "&reply_to_message_id={}".format(message_id)
    BOT.get_url(url)
    
def main():
    global waiting
    waiting = []
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        try:
            if len(updates["result"]) > 0:
                last_update_id = BOT.get_last_update_id(updates) + 1
                for update in updates["result"]:
                    if update_new_quests(update):
                        respond(update)
        except Exception as e:
            #print(e)
            pass
        sleep(0.5)

def update_new_quests(update):
    global waiting
    try:
        for quest in waiting:
            if not quest["from"] == get_sender(update):
                continue
            if is_button_response(update):
                check_waiting_buttons(update['callback_query'], quest)
                return False
            elif is_message_with_text(update):
                if "/reset" in update["message"]["text"]:
                    return True
                if quest["stage"] == "describe":
                    quest['description'] = update['message']['text']
                    quest['stage'] = 'reward'
                    BOT.send_message("Now please set the reward(s)",quest["from"])
                    return False
                elif quest['stage'] == 'reward':
                    quest['reward'] = update['message']['text']
                    quest['stage'] = 'title'
                    BOT.send_message("Now please give your sidequest a title",quest["from"])
                    return False
                elif quest["stage"] == "title":
                    quest['title'] = update['message']['text']
                    quest['stage'] = 'done'
                    BOT.send_message("Adding your sidequest to the sidequest board!",quest["from"])
                    send_options(update["message"]["from"]["id"], YESORNO,"Should I alert the chat of your sidequest?", message_id= update["message"]["message_id"])
                    return False
        if is_button_response(update):
            data = update["callback_query"]["data"]
            if "p?" in data:
                index = int(data.replace("p?",""))
                quest = get_quest(index)
                BOT.send_message("The chat was reminded about your sidequest: {}".format(quest["title"]),quest["from"])
                BOT.send_message("{} has not been completed yet. Complete this sidequest for the following rewards:\n{}".format(quest["title"],quest["reward"]), quest_chat)
                formatted = format_quest(json.dumps(quest)).replace("/n","<br>")
                send_options(quest_chat, gen_ACCEPT(index), formatted)
                return False
            elif "a?" in data:
                quest = get_quest(int(data.replace("a?","")))
                name = get_name(update["callback_query"]["from"])
                BOT.send_message("{} has claimed the sidequest {}".format(name, quest["title"]), update["callback_query"]["message"]["chat"]["id"])
                BOT.send_message("{} has accepted your sidequest: {}".format(name, quest["title"]), quest["from"])
                return False
            elif "r?" in data:
                index = int(data.replace("r?",""))
                quest = get_quest(index)
                if quest["from"] == update["callback_query"]["from"]["id"]:
                    remove_quest(index)
                    BOT.send_message("Your sidequest {} was removed.".format(quest["title"]),quest["from"])
                return False
            BOT.send_message("We couldn't locate your sidequest.\nMake a new one with /newquest or view your active sidequests with /myquests", update["callback_query"]["message"]["chat"]["id"])
    except Exception as e:
        #print("UPDATE ERROR: "+str(e))
        pass
    return True

def check_waiting_buttons(query, quest):
    global waiting
    data =  str(query['data'])
    if quest["stage"] == "anon":
        privacy = " public"
        quest['sponsor'] = get_name(query["from"])
        if data == "2":
            waiting.remove(quest)
            BOT.send_message("Ok your sidequest was canceled. :(".format(privacy),quest["from"])
        if data == '1':
            privacy = "n anonymous"
            quest['sponsor'] = "anon"
        BOT.send_message("Ok this will be posted as a{} sidequest.\nPlease send a description of the sidequest.".format(privacy),quest["from"])
        quest["stage"] = "describe"
    if quest["stage"] == "done":
        if data == '1':
            BOT.send_message("Ok, I will alert the sidequest chat for you!", quest["from"]) 
            BOT.send_message("A new sidequest ({}) was posted by {}:".format(quest["title"], quest["sponsor"]), quest_chat)
            file = open("data/quests.txt","r")
            quests = json.loads(file.readline())
            file.close()
            amount = len(quests)
            formatted = format_quest(json.dumps(quest)).replace("/n","<br>")
            send_options(quest_chat, gen_ACCEPT(amount), formatted)
        elif data == "2": 
            waiting.remove(quest)
            BOT.send_message("Ok the sidequest creation was canceled.", quest["from"])
        else:
            BOT.send_message("Ok it was added without notifying the chat.", quest["from"])
        quest["stage"] = "posted"
        add_quest(json.dumps(quest))
        waiting.remove(quest)
        
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

def is_button_response(update):
    try:
        update['callback_query']
    except Exception:
        return False
    return True

def is_message_with_text(update):
    try:
        update['message']['text']
    except Exception:
        return False
    return True

def get_sender(update):
    if is_message_with_text(update):
        return update['message']['from']['id']
    elif is_button_response(update):
        return update["callback_query"]['from']['id']


def format_quest(quest_string):
    quest = json.loads(quest_string)
    out = ""
    out += "<b>{}:</b>\n<b>Sponsor:</b>\t{}\n".format(quest["title"], quest["sponsor"])
    out += "<b>Description:</b>\n{}\n".format(quest["description"])
    out += "<b>Rewards:</b>\n{}".format(quest["reward"])
    return out

def user_has_waiting(user_id):
    for quest in waiting:
        if quest["from"] == user_id:
            return True
    return False

def view_quests(update, id = None):
    file = open("data/quests.txt","r")
    quests = json.loads(file.readline())
    file.close()
    if len(quests) == 0 and not id:
        quest_count(update)
        return
    i = 0
    count =0
    for quest in quests:
        if id:
            if update["message"]["from"]["id"] == json.loads(quest)["from"]:
                formatted = format_quest(quest).replace("/n","<br>")
                send_options(update["message"]["from"]["id"], gen_MINE(i), formatted, message_id = update["message"]["message_id"])
                count += 1
        else:
            formatted = format_quest(quest).replace("/n","<br>")
            send_options(update["message"]["chat"]["id"], gen_ACCEPT(i), formatted)
            count += 1
        i+=1
    if count == 0:
        BOT.send_message("You have no active sidequests.\nMake a new sidequest with /newquest\nor view others sidequests with /viewquests",update["message"]["from"]["id"])

def quest_count(update):
    file = open("data/quests.txt","r")
    quests = json.loads(file.readline())
    file.close()
    amount = len(quests)
    plural = "There are currently {} active sidequests!".format(amount)
    if amount == 1:
        plural = "There is 1 active sidequest!"
    if amount == 0:
        plural = "There are no active sidequests :(\nMake a new sidequest with /newquest"
    BOT.send_message(plural,update["message"]["chat"]["id"])

def add_quest(quest_string):
    file = open("data/quests.txt","r")
    quests = json.loads(file.readline())
    file.close()
    quests += [quest_string]
    file = open("data/quests.txt","w")
    file.write(json.dumps(quests))
    file.close()

def get_quest(index):
    file = open("data/quests.txt","r")
    quests = json.loads(file.readline())
    file.close()
    i = 0 
    target = ""
    for quest_string in quests:
        if i == index:
            target = quest_string
            return json.loads(quest_string)
            break
        i+=1
    return None

def remove_quest(index):
    file = open("data/quests.txt","r")
    quests = json.loads(file.readline())
    file.close()
    quests.pop(index)
    file = open("data/quests.txt","w")
    file.write(json.dumps(quests))
    file.close()

def respond(update):
    global waiting
    try:
        if "/newquest" in update["message"]["text"]:
            if not user_has_waiting(update["message"]["from"]["id"]):
                waiting += [{"from" : update["message"]["from"]["id"],"stage":"anon"}]
                send_options(update["message"]["from"]["id"], YESORNO,'Should this sidequest be anonymous?')
            else:
                BOT.send_message("You already have a sidequest in the middle of being created, please finish that process first. (or use /reset and try again.)", update["message"]["from"]["id"])
        if "/viewquests" in update['message']['text']:
            view_quests(update)
        if "/myquests" in update['message']['text']:
            if update["message"]["from"]["id"] != update["message"]["chat"]["id"]:
                BOT.send_message("You have to view your sidequests in DMs with the bot because it gets lonely :(", update["message"]["chat"]["id"])
                BOT.send_message("Hello there! To view your sidequests use /myquests!", update["message"]["from"]["id"])
            view_quests(update, id=True)
        if "/questcount" in update['message']['text']:
            quest_count(update)
        if "/help" in update['message']['text']:
            BOT.send_message(help_message,update["message"]["chat"]["id"])
        if "/reset" in update['message']['text']:
            for quest in waiting:
                if quest["from"] == update["message"]["from"]["id"]:
                    waiting.remove(quest)
            BOT.send_message("Your old sidequest draft was discarded. Use /newquest to make a new sidequest!", update["message"]["from"]["id"])
    except Exception as e:
        #print("RESPOND ERROR" + str(e))
        pass

if __name__ == '__main__':
    main()
