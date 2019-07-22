'''
This bot is used to contact Health Ads if someone needs them.
The bot automaticlly contacts all Health Ads that have registered if
some mention of healthads happens in a chat its in (see triggers)
'''

import json
from time import sleep
import urllib
from botbase_small import BotBase

file = open("data/token.txt")
URL = "https://api.telegram.org/bot{}/".format(file.read().close())
file.close()

BOT = BotBase(URL)
health_chat = -1001253468351 #-317228019 
waiting = []
help = []
urgent_list = {}
triggers = ["@healthads", "@healthad", "health ads", "/contact","/healthads", "health ad"]
start_message = "<b>If you are a person in need of help:</b>\nTo contact all the Health Ads use /contact\nIf you want to contact a specific Health Ad use /viewads to see all the registered Health Ads.\n\n<b>If you are a Health Ad:</b>\nTo register use /register./nTo remove yourself from the health ad list use /retire."
emergency_warning = "<b>If this is an emergency, call </b>626-395-5000<b> if you are on campus, and 911 otherwise.</b>\n\n"
help_message = '<b>Caltech Security Contacts:</b>\nCaltech Security Number:\n626-395-5000\nNon Urgent Security Number:\n626-395-4701\n\n<b>Commands</b>\n/urgent:\nSpams all Health Ads until one responds.\n/viewads:\nView all of the Health Ads and their information.\n/register:\nRegister as a Health Ad.\n/retire:\nRemove yourself from the Health Ads list.\n/help:\nShows usage info about the bot.'

def gen_RESPOND(data):
    return {'inline_keyboard': [[{'text' : 'I Cannot Respond', "callback_data":"oof"},{'text' : 'I Can Respond', 'callback_data':"re?" + str(data)}]]}

def send_options(chat_id, options, text, parse_mode = 'HTML', message_id = None):
    text = urllib.parse.quote_plus(text)
    keys = json.dumps(options)
    keys = urllib.parse.quote_plus(keys)
    url = URL + "sendMessage?text={}&chat_id={}&reply_markup={}&parse_mode={}".format(text,chat_id,keys,parse_mode)
    if message_id:
        url += "&reply_to_message_id={}".format(message_id)
    BOT.get_url(url)
   
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
    return name + get_user_name(user)

def get_user_name(user):
    try: 
        return " (@{})".format(user["username"])
    except:
        pass
    return ""

def is_dm(update):
    try:
        return update["message"]["from"]["id"] == update["message"]["chat"]["id"]
    except:
        pass
    return False

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

def user_has_waiting(user_id):
    for quest in waiting:
        if quest["from"] == user_id:
            return True
    return False

def is_command(update, command):
    try:
        return command in update["message"]["text"]
    except Exception as e:
        pass
    return False

def is_call_for_help(update):
    try:
        for call in triggers:
            if call in update["message"]["text"]:
                return True
    except Exception as e:
        pass
    return False

def format_health_ad(ad):
    return "{} lives in room {}.\nContact them at: {}\n\n".format(ad["name"], ad['room'], ad["phone"])

def format_health_ads():
    file = open('data/health_ads.txt', "r")
    data = json.loads(file.readline())
    file.close()
    out = ""
    for key in data:
        out += format_health_ad(data[key])
    return out

def get_ad_phone(id):
    file = open('data/health_ads.txt', "r")
    data = json.loads(file.readline())
    file.close()
    for ad_id in data:
        if str(ad_id)== str(id):
            return data[ad_id]["phone"]
    return "911"

def add_data(info, location):
    file = open(location, "r")
    data = json.loads(file.readline())
    file.close()
    data[info["from"]] = info
    file = open(location, "w")
    file.write(json.dumps(data))
    file.close()

def remove_data(id, location):
    file = open(location, "r")
    data = json.loads(file.readline())
    file.close()
    for ad in data:
        if str(ad) == str(id):
            data.pop(ad)
            break

    file = open(location, "w")
    file.write(json.dumps(data))
    file.close()

def get_distress_name_from_text(text):
    if text.split("\n")[3].strip() == "Person in distress:":
        return text.split("\n")[4].strip()
    return text.split("\n")[3].strip()

def send_message_to_all(text):
    BOT.send_message(text, health_chat)
    file = open('data/health_ads.txt', "r")
    data = json.loads(file.readline())
    file.close()
    for ad_id in data:
        BOT.send_message(text, ad_id)

def send_distress(distress_call, urgent = False):
    formatted = ""
    formatted += "<b>Can you respond to this summons?</b>\n\n"
    formatted += "<b>Person in distress:</b>\n{}\n".format(distress_call["name"])
    formatted += "<b>Level of urgency:</b>\n{}\n".format(distress_call["urgency"])
    formatted += "<b>Reason for the call</b>\n{}\n".format(distress_call["event"])
    formatted += "<b>Their location:</b>\n{}\n".format(distress_call["location"])
    if set_urgent_message(distress_call["from"], "temp", "filling"):
        formatted = "<b>!!THIS IS URGENT!!</b>\n" + formatted
        set_urgent_message(distress_call["from"],formatted,"filled")
    file = open('data/health_ads.txt', "r")
    ads = json.loads(file.readline())
    file.close()
    send_options(health_chat, gen_RESPOND(distress_call["from"]), formatted)
    for ad_id in ads:
        send_options(ad_id, gen_RESPOND(distress_call["from"]), formatted)

def format_phone_number(text):
    numbers = "1234567890"
    out = text
    for c in text:
        if c not in numbers:
            out.replace(c, "")

    return "({}) {}-{}".format(out[0:3],out[3:6],out[6:10])

def start_help(update, urgent = False):
    global help
    global urgent_list
    #global spam
    BOT.send_message("The Health Ads have been notified that you may require help.\nPlease describe what has happened.", update["message"]["from"]["id"])
    help += [{"from" : update["message"]["from"]["id"], "stage":"event", "name": get_name(update["message"]["from"])}]
    if not urgent:
        send_message_to_all("{} is calling for a Health Ad!\nMessage:\n{}\nMore information will be coming soon.".format(get_name(update["message"]["from"]), update["message"]["text"]))
    if urgent:
        send_message_to_all("<b>URGENT</b>\n{} is calling for a Health Ad!\nMessage:\n{}\nMore information will be coming soon.".format(get_name(update["message"]["from"]), update["message"]["text"]))
        urgent_list[update["message"]["from"]["id"]] = {"message":"<b>URGENT</b>\n{} is calling for a Health Ad!\nMessage:\n{}\nMore information will be coming soon.".format(get_name(update["message"]["from"]),update["message"]["text"]), "stage" : "filling"}

def urgent_prompt():
    for urgent in urgent_list:
        if urgent_list[urgent]["stage"] == "filling":
            send_message_to_all(urgent_list[urgent]["message"])
            set_urgent_message(urgent, "oof", "oof")
        elif urgent_list[urgent]["stage"] == "filled":
            send_options(health_chat, gen_RESPOND(urgent), urgent_list[urgent]["message"])
            file = open('data/health_ads.txt', "r")
            ads = json.loads(file.readline())
            file.close()
            for ad_id in ads:
                send_options(ad_id, gen_RESPOND(urgent), urgent_list[urgent]["message"])
            

def set_urgent_message(id, message, stage):
    global urgent_list
    try:
        urgent_list[id]["message"] += ""
        urgent_list[id]["message"] = message
        urgent_list[id]["stage"] = stage
        return True
    except KeyError as e:
        pass
    return False

def remove_urgent(id, d_name, name, respond_id):
    global urgent_list
    message = ''
    try:
        message = urgent_list.pop(int(id))
    except KeyError as e:
        BOT.send_message("It seems that this urgent call was already answered.", respond_id)
        return 
    BOT.send_message("{} is able to answer the urgent call from {}.".format(name, d_name), health_chat)

def respond(update):
    global waiting
    global help
    try:
        if is_button_response(update):
            data = update["callback_query"]["data"]
            if "re?" in data:
                in_need_id = data.replace("re?","")
                call = get_ad_phone(update["callback_query"]["from"]["id"])
                name = get_distress_name_from_text(update["callback_query"]["message"]["text"])
                helper = get_name(update["callback_query"]["from"])
                BOT.send_message("{} is able to come help!\nContact them at {}".format(helper, call), in_need_id)
                BOT.send_message("{} has been notified that you can help!".format(name), update["callback_query"]["from"]["id"])
                if set_urgent_message(int(in_need_id), "", "over"):
                    remove_urgent(in_need_id, name, helper, update["callback_query"]["from"]["id"])
            return
        if is_call_for_help(update):
            BOT.send_message(emergency_warning, update["message"]["chat"]["id"])
            if not is_dm(update):
                BOT.send_message("Please message me about your situation at @DabneyHealthAdBot.",update["message"]["chat"]["id"])
                BOT.send_message("To send a call for a Health Ad please use /contact",update["message"]["from"]["id"])
            else:
                start_help(update)
            return
        if is_command(update, "/register"):
            if not is_dm(update):
                BOT.send_message("Please DM me your information at @DabneyHealthAdBot so I have permission to DM you.", update["message"]["chat"]["id"])
                BOT.send_message("If you would like to register as a Health Ad use /register!", update["message"]["from"]["id"])
                return
            if not user_has_waiting(update["message"]["from"]["id"]):
                waiting += [{"from" : update["message"]["from"]["id"],"stage":"room","name": get_name(update["message"]["from"])}]
                BOT.send_message("Thank you for registering as a Health Ad! Please supply the requested information so that you can be contacted when someone needs a Health Ad. First of all, what is your room number?", update["message"]["from"]["id"])
            else:
                BOT.send_message("You already have an account in the middle of being created, please finish that process first. (or use /reset and try again.)", update["message"]["from"]["id"])
                return
        elif is_command(update, "/viewads"):
            BOT.send_message(emergency_warning,update["message"]["chat"]["id"])
            BOT.send_message(format_health_ads(),update["message"]["chat"]["id"])
            return
        elif is_command(update, "/help"):
            BOT.send_message(emergency_warning,update["message"]["chat"]["id"])
            BOT.send_message(help_message, update["message"]["chat"]["id"])
            return
        elif is_command(update, "/retire"):
            remove_data(update["message"]["from"]["id"], 'data/health_ads.txt')
            BOT.send_message("You have been removed as a health ad :(", update["message"]["chat"]["id"])
            return
        elif is_command(update, "/urgent"):
            BOT.send_message(emergency_warning,update["message"]["chat"]["id"])
            if not is_dm(update):
                BOT.send_message("Please message me about your situation at @DabneyHealthAdBot.",update["message"]["chat"]["id"])
            start_help(update, urgent=True)
        elif is_command(update, "/reset"):
            for ad in waiting:
                if ad["from"] == update["message"]["from"]["id"]:
                    waiting.remove(ad)
            BOT.send_message("Your registration draft was discarded. Use /register to register as a health ad!", update["message"]["from"]["id"])
            return
        elif is_command(update, "/start") and is_dm(update):
            BOT.send_message(emergency_warning, update["message"]["from"]["id"])
            BOT.send_message(start_message, update["message"]["from"]["id"])
        elif is_dm(update):
            start_help(update)

    except Exception as e:
        # print("RESPOND ERROR" + str(e))
        raise(e)
        pass

def update_register(update):
    global waiting
    try:
        for ad in waiting:
            if not ad["from"] == get_sender(update):
                continue
            if is_message_with_text(update):
                if "/reset" in update["message"]["text"]:
                    return True
                if ad["stage"] == "room":
                    ad['room'] = update['message']['text']
                    ad['stage'] = 'phone'
                    BOT.send_message("Now please set your phone number", ad["from"])
                    return False
                elif ad["stage"] == "phone":
                    ad["phone"] = update['message']['text']
                    ad['stage'] = 'done'
                    add_data(ad,'data/health_ads.txt')
                    BOT.send_message("You are now registered as a health ad. use /retire to undo this.", ad["from"])
                    waiting.remove(ad)
                    return False
    except Exception as e:
        # print("UPDATE ERROR: "+str(e))
        raise(e)
        pass
    return True
    
def update_help(update):
    global help
    try:
        for dis in help:
            if not dis["from"] == get_sender(update):
                continue
            if is_message_with_text(update):
                if "/reset" in update["message"]["text"]:
                    help.remove(dis)
                    return False
                if dis["stage"] == "event":
                    dis['event'] = update['message']['text']
                    dis['stage'] = 'location'
                    BOT.send_message("Where are you currently? Or where will you be?", dis["from"])
                    return False
                elif dis["stage"] == "location":
                    dis['location'] = update['message']['text']
                    dis['stage'] = 'urgency'
                    BOT.send_message("How urgent is your situation?", dis["from"])
                    return False
                elif dis["stage"] == "urgency":
                    dis["urgency"] = update['message']['text']
                    dis['stage'] = 'done'
                    send_distress(dis)
                    BOT.send_message("All Health Ads have been notififed of your situation!", dis["from"])
                    help.remove(dis)
                    return False
    except Exception as e:
        # print("UPDATE HELP ERROR: "+str(e))
        raise(e)
        pass
    return True
        
def main():
    global waiting
    waiting = []
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        urgent_prompt()
        try:
            if len(updates["result"]) > 0:
                last_update_id = BOT.get_last_update_id(updates) + 1
                #continue
                for update in updates["result"]:
                    if update_register(update) and update_help(update):
                        respond(update)
        except Exception as e:
            raise(e)
            pass
        sleep(0.5)

if __name__ == '__main__':
    main()
