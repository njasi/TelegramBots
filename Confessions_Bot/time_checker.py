import time
import json

file = open('data/messages.txt','r')
lines = file.readlines()
if len(lines) != 1:
    print('There are currently {} messages in the queue.'.format(len(lines)))
else:
    print('There is currently one message in the queue.')
for line in lines:
    message = json.loads(line.strip())
    print('Time to send: {} seconds.'.format(int(message['send_time']) - int(time.time())))
file.close()
