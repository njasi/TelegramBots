'''
This bot is able to search for anime and provide you with a link to watch an episode.
It searches through gogoanime.io / gogoanimes.tv to find what it needs.

I made this just because I can...
also its convient if you can't find an episode on your own
'''

import json, requests, time, urllib, string, bs4
from botbase import BotBase
from random import random

DOWNLOAD_NUM = 0
DOWNLOAD_STRINGS =["https://www5.gogoanime.io/{}-episode-{}","https://www.gogoanimes.tv/{}-episode-{}"]

from requests_html import HTMLSession
current = 0
ep_requests = {} # user_id: url_name

# i'm probably dumb but this works
def get_attribute_from_nav_str(nav_str, attr, start = '="', end = '"', smallest = 3):
    string_rep = str(nav_str.encode('utf-8'))
    data_index = string_rep.find(attr + start) + len(start) + len(attr)
    out = string_rep[data_index:string_rep.find(end, data_index)]
    if len(out) > smallest:
        return out
    return None

###############
# Rapid video #
###############

def url_rv(url):
    res = requests.get(url)
    res.raise_for_status()
    thing = bs4.BeautifulSoup(res.text, features="html.parser")
    res.close()
    for child in thing.select(".rapidvideo")[0].children:
        data_vid = get_attribute_from_nav_str(child, "data-video")
        if data_vid:
            return data_vid

def source_rv(url):
    res = requests.get(url)
    res.raise_for_status()
    string = str(res.content)
    if "You have watched over 60 minutes of video today." in string:
        amount = string[string.find("Please wait ")+12:string.find(" minutes or ")]
    res.close()
    start_i = string.find('source src="') + 12
    out = string[start_i:string.find('"', start_i)]
    return out

def get_video_url(ep_num, name, type = 0):
    url = DOWNLOAD_STRINGS[type].format(name, ep_num)
    source_url = source_rv(url_rv(url))
    return source_url

########################
# Search Functionality #
########################

def search(name):
    search_data = []
    url = "https://www5.{}//search.html?keyword={}".format("gogoanime.io",name)
    res = requests.get(url)
    results = bs4.BeautifulSoup(res.text, features="html.parser")
    res.close()

    for child in results.select(".items")[0].children:
        title = get_attribute_from_nav_str(child, "title")
        if title == None:
            continue
        url = get_attribute_from_nav_str(child, "href")
        image = get_attribute_from_nav_str(child, "src")
        search_data += [{"name": title, "url_name": url.replace("/category/",""), "image": image}]
    return search_data

##########################
# Get info From url_name #
##########################

def get_info(url_name):
    url = "https://www6.gogoanime.io/category/{}".format(url_name)
    res = requests.get(url)
    results = bs4.BeautifulSoup(res.text, features="html.parser")
    res.close()
    image = None
    name = None
    start = 0
    end = 0
    for child in results.select(".anime_info_body_bg img"):
        test = get_attribute_from_nav_str(child,"src")
        if len(test) > 6:
            image = test
    for child in results.select(".anime_info_body_bg h1"):
        name = get_attribute_from_nav_str(child,">",start = "",end = "</")
    for thing in results.select("#episode_page li"):
        start_test = int(get_attribute_from_nav_str(thing,"ep_start",smallest = 0))
        end_test = int(get_attribute_from_nav_str(thing,"ep_end",smallest = 0))
        if start > start_test:
            start = start_test
        if end < end_test:
            end = end_test
    range_eps = "{}-{}".format(start,end)
    if not image:
        image = "https://png.pngtree.com/element_pic/17/02/23/8a1ce248ab44efc7b37adad0b7b2d933.jpg"
    return (image, name, range_eps)

###########################
# Bot Related Stuff Below #
###########################
file = open("token.txt")
BOT = BotBase(file.read().strip())
file.close()
help_message = '<b>Commands:</b>\n/search: Search for an anime\n/help: Get help...'

##################
# Helper Methods #
##################

def get_user_name(user):
    name = ''
    try:
        name = user["username"]
    except Exception:
        name = get_game(user)
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

def is_thing(update,keys):
    try:
        test = update
        for key in keys:
            update = update[key]
    except Exception:
        return False
    return True

#####################
# Buttons and Stuff #
#####################

def gen_RESULTS(results):
    buttons = []
    for res in results:
        buttons += [[{
            "text": res["name"],
            "callback_data": res["url_name"]
            }]]
    boi = {"inline_keyboard":buttons}
    return boi

def send_options(chat_id, options, text, parse_mode = 'HTML', message_id = None):
    text = urllib.parse.quote_plus(text)
    keys = json.dumps(options)
    keys = urllib.parse.quote_plus(keys)
    url = BOT.URL + "sendMessage?text={}&chat_id={}&reply_markup={}&parse_mode={}".format(text,chat_id,keys,parse_mode)
    if message_id:
        url += "&reply_to_message_id={}".format(message_id)
    BOT.get_url(url)

def send_anime_info(chat_id, caption, url_name, parse_mode = 'HTML'):
    info = get_info(url_name)
    photo_url = info[0]
    name = info[1]
    range_eps = info[2]
    caption = urllib.parse.quote_plus(caption.format(name, range_eps))
    url = BOT.URL + "sendPhoto?chat_id={}&photo={}".format(chat_id, photo_url)
    url += "&caption={}".format(caption)
    url += "&parse_mode={}".format(parse_mode)
    boi = {"force_reply": True, "selective":True}
    url += "&reply_markup={}".format(urllib.parse.quote_plus(json.dumps(boi)))
    BOT.get_url(url)
    return range_eps

def parse_range(boi):
    splitt = boi.split("-")
    return (int(splitt[0]),int(splitt[1]))

def ep_in_range(range_string,ep):
    ep = int(ep)
    real_range = parse_range(range_string)
    return ep > real_range[0] and ep <= real_range[1]
    
###########################
# Bot response controller #
###########################

def respond(update):
    global waiting

    if is_thing(update, ['callback_query']):
        data = update['callback_query']["data"]
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        range = send_anime_info(chat_id, "What episode of {} do you want? ({})\n(reply to this message)", data)
        ep_requests[str(update['callback_query']["from"]["id"])] = (data, range)
    
    elif is_thing(update, ['message', 'text']):
        text = update["message"]["text"]
        chat_id = update["message"]["chat"]["id"]
        user_id = update["message"]["from"]["id"]
        message_id = update["message"]["message_id"]

        # check if its a response to a search
        if is_thing(update, ['message', 'reply_to_message']):
            reply_text = None
            try:
                reply_text = update["message"]["reply_to_message"]["text"]
            except:
                reply_text = update["message"]["reply_to_message"]["caption"]

            if reply_text == "What do you want to search for? (respond to this message)":
                response_text = "Search results:"
                send_options(chat_id,gen_RESULTS(search(text)),response_text, message_id = update["message"]["message_id"])
            elif "What episode of " in reply_text:
                url_string = None
                try:
                    if ep_in_range(ep_requests[str(user_id)][1],text):
                        url_string = get_video_url(text, ep_requests[str(user_id)][0])
                    else:
                        BOT.send_message("Please request an episode within the range {}.".format(ep_requests[str(user_id)][1]), chat_id)
                except KeyError:
                    BOT.send_message("Please try selecting the anime again by tapping the search button corresponding to it.", chat_id)
                    return
                name = reply_text[16: reply_text.find(" do you want?")]
                message_boi = "Here is Ep {} of {}!\n{}".format(text,name,url_string)
                BOT.send_message(url_string, chat_id)
        if "/search" in text:
            BOT.send_reply("What do you want to search for? (respond to this message)", \
                           chat_id, message_id, force_reply = True)
        if "/help" in text:
            BOT.send_message(help_message, chat_id)

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
                        print(e)
                else:
                    respond(update)
        time.sleep(0.5)

if __name__ == '__main__':
    main()