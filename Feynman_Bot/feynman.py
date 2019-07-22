import json
import requests
import time
import wolframalpha
import wikipedia
import botbase # so I don't have to rewrite everything every time

QUIT = False
BOT = botbase("https://api.telegram.org/bot{}/".format(TOKEN))

reader = open('token.txt','r')
TOKEN = reader.readline().strip()
reader = open('wolfram.txt','r')
app_id = reader.readline().strip()
reader.close()
client = wolframalpha.Client(app_id)

def main():
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = BOT.get_last_update_id(updates) + 1
            if(QUIT):
                quit()
            respond(updates)
        time.sleep(0.5)

def respond(updates):
    for update in updates["result"]:
        try:
            respond_smart(update['message'])
        except Exception as e:
            # raise(e)
            pass

def respond_smart(update):
    global QUIT
    text = update["text"]
    chat = update["chat"]["id"]
    reply_id = update["message_id"]

    if(text == "/QUIT"):
        QUIT = True

    if not "@RichardFeynmanBot" in text:
        return 
    text = ("".join(text.split("@RichardFeynmanBot"))).strip()

    r = search(text)

    if r[0] == None:  # unable to find anything
        BOT.send_reply('That\'s a dumb question.', chat, reply_id)
        return
    if r[1] != None: # if it finds an image it will send it with the caption  #TODO: caption has a char limit of 1024
        BOT.send_reply_with_photo(r[0], r[1], chat, reply_id)
        return
    BOT.send_reply(r[0],chat,reply_id) # if there is not an image but it does find somthing
    return

def search(text = ''):
  res = client.query(text)
  if res['@success'] == 'false':
     return search_wiki(text), primaryImage(text)
  else:
    result = ''
    pod0 = res['pod'][0]
    pod1 = res['pod'][1]
    if (('definition' in pod1['@title'].lower()) or ('result' in  pod1['@title'].lower()) or (pod1.get('@primary','false') == 'true')):
        result = resolveListOrDict(pod1['subpod'])
        question = resolveListOrDict(pod0['subpod'])
        question = removeBrackets(question)
        return result, primaryImage(question)
    else:
        question = resolveListOrDict(pod0['subpod'])
        question = removeBrackets(question)
        return search_wiki(question), primaryImage(question)

def search_wiki(query):
    result = wikipedia.search(query)
    if not result:
        return
    try:
        page = wikipedia.page(query)
        answer = wikipedia.summary(query, sentences=2)
        if '==' in answer:
            answer = wikipedia.summary(query, sentences=1)
    except wikipedia.DisambiguationError as err:
        page = wikipedia.page(err.options[0])
        answer = wikipedia.summary(err.options[0], sentences=2)
        if '==' in answer:
            answer = wikipedia.summary(query, sentences=1)
    except wikipedia.PageError as err:
        answer = None
    return answer

def removeBrackets(variable):
    return variable.split('(')[0]

def resolveListOrDict(variable):
    if isinstance(variable, list):
        return variable[0]['plaintext']
    else:
        return variable['plaintext']

def primaryImage(title=''):
    url = 'http://en.wikipedia.org/w/api.php'
    data = {'action':'query', 'prop':'pageimages','format':'json','piprop':'original','titles':title}
    try:
        res = requests.get(url, params = data)
        key = list(res.json()['query']['pages'].keys())[0]
        imageUrl = res.json()['query']['pages'][key]['original']['source']
        return imageUrl
    except Exception as err:
        return None

if __name__ == '__main__':
    main()