import json, time, urllib, requests, botbase
from PIL import Image
from random import randint
from math import ceil
from io import BytesIO

# Image.getpixel(xy)

QUIT = False

file = open("data/token.txt")
TOKEN = file.read().strip()
file.close()
BOT = botbase.BotBase(TOKEN)

def get_main_chat():
    file = open("data/chat_id.txt")
    num = int(file.read().strip())
    file.close
    return num

CHESS_CHAT = get_main_chat()

help_message = "<b>Commands:</b>\n/newgame:\n    Send in a request for a new game.\n/leaderboard:\n    View the different leaderboards.\n/viewgames:\n    View any currently active games.\n/replay:\n    Allows you to watch old games.\n/help:\n    H M M S T  idk what this does.\n\n<b>Gameplay:</b>\nOnce a game starts you take your move by replying to the message sent to your dms. The move positions use the grid given on the image.\n    Move EX: a3 to a5\nIf your message is not formatted like this it will not work (A3 to A5 is still valid)."

checkers = ("⬜","⬛")
tileset = { -1: False, 0: "♙", 1: "♖", 2: "♘", 3: "♗", 4: "♔", 5: "♕", 6: "♟", 7: "♜", 8: "♞", 9: "♝", 10: "♚", 11: "♛",}
images = {-1: False, 0: 'pawnw', 1: 'rookw', 2: 'knightw', 3: 'bishopw', 4: 'kingw', 5: 'queenw', 6: 'pawnb', 7: 'rookb', 8: 'knightb', 9: 'bishopb', 10: 'kingb', 11: 'queenb'}



########
# TODO #
########
'''
send game requests exclusivly to the chess chat

test if the bot can dm a person (require dm somehow)
    do this before a request is accepted or sent (will be helpful)

flip the board so its like the players are facing eachother?
    reverse all items in a row then reverse all rows
    dont forget sidelined pieces

leaderboard saving after game finishes
    win/loss screen
    inform chat of the result with info (see move history)

help message

rules message

view current games
    check the games list and give info
    allow recreation

keep a move history for the chess board
    view history at anytime?
    recreate chess games
    (use to do the one pawn attack)
    when game is over send this info in some format that can be read in a message so it can be recreated for a replay (let's not do image data)

validate pieces moves
    collisions
    destroying pieces
    king movement = limited queen movement plus checks
    knight movement
    pawn attacking/not attacking
    make move without messages
    check that it's the correct player moving a piece
    queen move = rook/bishop

pawn promotion
    select piece wanted
        probably send a special keyboard for this
    
castling
    check move history?
    how to call on it?
    cannot castle out of or into check

if a move is incorrect display possible moves on the response back
    include a way to request anyway (like /moves a3 or somthing)

keeping a list of destroyed pieces and displaying it
    (probably to the left)
    use smaller icons?

'''

###############################
# Chess Board Class And Stuff #
###############################

def rgb_sum(pixel):
    return pixel[0] + pixel[1] + pixel[2]

def get_num_from_image(update):
    try:
        files = update["message"]["reply_to_message"]["photo"]
        file_id = files[len(files) - 1]["file_id"]
        data = BOT.get_file(file_id)
        path = data["result"]["file_path"]
        response = requests.get("https://api.telegram.org/file/bot{}/{}".format(BOT.TOKEN, path))
        img = Image.open(BytesIO(response.content))
        binary = []
        for i in range(900):
            if rgb_sum(img.getpixel((i,0))) > 682:
                binary += ["0"]
            else:
                binary += ["1"]
        binary.reverse()
        bin_string = "".join(binary)
        bin_string = str(int(bin_string))
        amount = 1
        sum = 0
        for i in range(len(bin_string)):
            sum += int(bin_string[(len(bin_string) - 1) - i]) * amount
            amount *= 2
        return sum
    except Exception as e:
         return -1

class ChessBoard:
    def __init__(json):
        self.board = json["board"]
        self.names = json["names"]
        self.number = json["number"]
        self.offset = json["offset"]
        self.p_ids = json["players"]
        self.size = json["size"]
        self.stage_path = json["stage_path"]
        self.turn = json["turn"]
        self.turn_num = json["turn_num"]

    def __init__(self, player_ids, names, json = None):
        self.MOVE_DICT = {
        -1:self.empty,
        0:self.white_pawn_move,
        1:self.rook_move,
        2:self.knight_move,
        3:self.bishop_move,
        4:self.king_move,
        5:self.queen_move,
        6:self.black_pawn_move,
        7:self.rook_move,
        8:self.knight_move,
        9:self.bishop_move,
        10:self.king_move,
        11:self.queen_move}

        if json:
            self.board = json["board"]
            self.names = json["names"]
            self.number = json["number"]
            self.offset = json["offset"]
            self.p_ids = json["players"]
            self.size = json["size"]
            self.stage_path = json["stage_path"]
            self.turn = json["turn"]
            self.turn_num = json["turn_num"]
        else:
            self.number = get_game_num()
            self.names = names
            increment_game_num()
            self.p_ids = player_ids
            self.turn = True # true = white (index 1 of names and players)
            self.turn_num = 0
            self.board = [
                [7, 8, 9, 11, 10, 9, 8, 7],
                [6, 6, 6, 6, 6, 6, 6, 6],
                [-1, -1, -1, -1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1, -1, -1, -1],
                [-1, -1, -1, -1, -1, -1, -1, -1],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [1, 2, 3, 5, 4, 3, 2, 1]
            ]
            # stuff to deal with image sizing
            scale = 1
            self.offset = (88 * scale, 88 * scale)
            self.size = 90 * scale
            num = randint(-1, 100)
            if num < 2:
                self.stage_path = "graphics/boards/{}.png".format(num)
            else:
                self.stage_path = "graphics/boards/2.png"
            self.stage_path = "graphics/boards/-1.png" # for testing purposes

    def translate(self, id, pos):
        out = tileset[id]
        if out:
            return tileset[id]
        if (pos[0] + pos[1]) % 2 == 0:
            return checkers[0]
        else:
            return checkers[1]

    def to_string(self):
        x,y = 0, 0
        out = "Player {}'s turn!\n".format(1 if self.turn else 2)
        for row in self.board:
            x = 0
            for item in row:
                out += self.translate(item, (x,y))
                x += 1
            y += 1
            out += "\n"
        return out

    def to_binary(self, n):
        out = ""
        if n > 1:
            out += self.to_binary(n//2) + ","
        return out + str(n % 2)

    def get_reversed_binary(self, n):
        oof = self.to_binary(n)
        oof = oof.split(",")
        oof.reverse()
        return "".join(oof)

    def to_image(self, show = False):
        im = Image.open(self.stage_path)
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                image_src = images[self.board[i][j]]
                if image_src:
                    pos = (j * self.size + self.offset[1], i * self.size + self.offset[0])
                    tile = Image.open("graphics/pieces/png/{}.png".format(image_src))
                    im.paste(tile, box = pos, mask = tile)
        num = self.get_reversed_binary(self.number)
        for i in range(len(num)):
            if num[i] == "1":
                im.putpixel((i,0), (200, 200, 200))
            if num[i] == "0":
                im.putpixel((i,0), (255, 255, 255))
        
        if show:
            im.show()
        return im

    def send_board(self,chat_id, your_turn = False, text = True):
        image = self.to_image()
        force_reply = True
        cap = ''
        if your_turn:
            cap = "Your move was sent to {}!".format(self.names[1] if self.turn else self.names[0])
            force_reply = False
        else:
            cap = "{} vs {} turn {}! (Game {}) \nreply to this to take your move!".format(self.names[0],self.names[1],self.turn_num,self.number)
        if not text:
            cap = ""
        send_photo_from_file(chat_id, image, caption = cap, force_reply = force_reply)

    ####################
    # Movement helpers #
    ####################

    def decode_move(self, move_str):
        move_str = move_str.lower()
        alpha = "abcdefgh"
        sp = move_str.split(" to ")
        try:
            one = (alpha.find(sp[0][0]), int(sp[0][1:])-1)
            two = (alpha.find(sp[1][0]), int(sp[1][1:])-1)
        except ValueError:
            return None
        if (self.validate_point(one) and self.validate_point(two)):
            return (one,two)   
        else:
            return None

    def get_piece(self, pos):
        return self.board[pos[1]][pos[0]]

    def add_points(self, one, two):
        return (int(one[0] + two[0]), int(one[1] + two[1]))

    def subtract_points(self, one, two):
        return (one[0] - two[0], one[1] - two[1])

    def is_friendly(self,piece):
        # 0-5 are white and 6-12 are black
        # if turn: its whites turn
        if self.turn:
            return piece > -1 and piece < 6
        else:
            return piece < 12 and piece >5

    def can_occupy(self, piece):
        if piece == -1:
            return(True, None) # there's no piece here
        elif not self.is_friendly(piece):
            return (True, "You've captured an enemy piece!")
        else: 
            return (False, "You cannot capture your own piece.")

    def is_safe(self, pos):
        return True

    #########################
    # Unique Piece Movement #
    #########################

    def rook_move(self, start_pos, end_pos):
        # checking that this is a valid rook move in general
        direction = (0,0)
        size = 0
        if start_pos[0] == end_pos[0] and start_pos[1] != end_pos[1]:
            direction = (0,1 * (size/(start_pos[1] - end_pos[1])))
            size = abs(start_pos[1] - end_pos[1])
        elif start_pos[1] == end_pos[1] and start_pos[0] != end_pos[0]:
            size = abs(end_pos[0] - start_pos[0])
            direction = (1 * (size/(end_pos[0] - start_pos[0])),0)
        else:
            return (False, "This is not a valid move for a rook.")
        # movement loop below
        place = start_pos
        for i in range(size - 1):
            place = self.add_points(place, direction)
            piece = self.get_piece(place)
            if piece != -1: # there's something in the way
                return (False, "There appears to be something in the way.")
        place = self.add_points(place, direction) # final spot
        piece = self.get_piece(place) # piece of the last spot
        # checking the final piece
        return self.can_occupy(piece)
        
    def knight_move(self, start_pos, end_pos):
        # check it's a valid knight move
        change = self.subtract_points(start_pos,end_pos)
        mag = (abs(change[0]), abs(change[1]))
        if (mag[1] == 2 and mag[0] ==1) or (mag[0] ==2 and mag[1] == 1):
            piece = self.get_piece(end_pos)
            return self.can_occupy(piece)
        return (False, "This is not a valid move for a knight.")

    def bishop_move(self, start_pos, end_pos):
        dis = self.subtract_points(start_pos, end_pos)
        if dis[1] != 0 and abs(dis[0]/dis[1]) == 1:
            change = (-1 * int(dis[0]/abs(dis[0])), -1 * int(dis[1]/abs(dis[1])))
            current = start_pos
            for i in range(abs(dis[0]) - 1):
                current = self.add_points(current, change)
                if self.get_piece(current) != -1:
                    return (False, "There appears to be something in the way")

            current = self.add_points(current, change) # final spot
            piece = self.get_piece(current) # piece of the last spot
            return self.can_occupy(piece) #can capture? or stand?
        return (False, "This is not a valid move for a bishop.")

    def queen_move(self, start_pos, end_pos):
        rook = self.rook_move(start_pos,end_pos)
        bishop = self.bishop_move(start_pos,end_pos)
        if rook[0]:
            return rook
        if bishop[0]:
            return bishop
        return(False, "This is not a valid move for a queen.")

    def king_move(self, start_pos, end_pos):
        # check that the movement itself is fine
        change = self.subtract_points(start_pos,end_pos)
        mag = (abs(change[0]), abs(change[1]))
        if (mag[0] == 1 and mag[1] ==1) or (mag[0] == 1 and mag[1] == 0) or (mag[1] == 1 and mag[0] ==  0):
            queen = self.queen_move(start_pos, end_pos)
            if not queen[0]:
                return (False, "This is not a valid move for a king.")
        else:
            return (False, "This is not a valid move for a king.")
        # now deal with check and shit
        # make an is_safe() function
        if self.is_safe(end_pos):
            return (True, None)
        return (False, "You cannot move your king into check")

    def white_pawn_move(self, start_pos, end_pos):
        # moves up the board (to lower values)
        change = self.subtract_points(start_pos, end_pos)
        if start_pos[1] == 6: # has not moved at all
            pass
        return(True,None)

    def black_pawn_move(self, start_pos, end_pos):
        # moves down the board (to higher values)
        
        return(True,None)

    def empty(self, start_pos, end_pos):
        return (False,"You tried to move a space without a piece...")

    def test_move(self, start, finish):
        # special cases:
        # pawn attacking 
        # king checking 
        piece = self.get_piece(start)
        if start in self.get_current_player_pieces(): # test to see if its the players piece
            function =  self.MOVE_DICT[piece]
            return function(start,finish)
        return (False, "You cannot move your opponent's piece")

    def make_move(self, move_str, chat_id, move_tuple = None, send = True):
        move = None
        if move_tuple:
            move = move_tuple
        else:
            move = self.decode_move(move_str)
        if move:
            test = self.test_move(move[0], move[1])
            print("MOVE RESULTS:\t", test)
            if test[0]:
                piece = self.board[move[0][1]][move[0][0]]
                king = self.get_current_player_pieces(targets = [4] if self.turn else [10])
                if not self.is_safe(king):
                    self.undo_move()
                    BOT.sendMessage("You cannot move into check!")
                    return False
                if piece == -1:
                    if send:
                        BOT.send_message("There is not a piece at {}.".format(move_str.split(" to ")[0]))
                    return False
                self.board[move[1][1]][move[1][0]] = piece
                self.board[move[0][1]][move[0][0]] = -1
                self.send_board(self.p_ids[0] if self.turn else self.p_ids[1])
                return True 
            elif send:
                BOT.send_message(test[1], chat_id)
                return False
        if send:
            BOT.send_message("Your move command was incorrect.\nEx: 'a1 to a3'", chat_id)
        return False

    def process_move(self, move_str,chat_id_user):
        print(move_str)
        chat_id = self.p_ids[1] if self.turn else self.p_ids[0]
        if str(chat_id) != str(chat_id_user):
            BOT.send_message("Wait your turn please. If you'd like you can view other games with /viewgames.", chat_id_user)
            return False
        if self.make_move(move_str, chat_id):
            self.turn = not self.turn
            self.turn_num += 1
            self.send_board(self.p_ids[0] if self.turn else self.p_ids[1], your_turn = True)
            return True
        else:
            self.send_board(self.p_ids[1] if self.turn else self.p_ids[0], your_turn=False)
        return False
            

    ##################
    # Checkmate shit #
    ##################

    def undo_move():
        pass

    def get_current_player_pieces(self, targets = None):
        pieces = []
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if targets and self.get_piece((j,i)) in targets:
                    return (j,i)
                else:
                    if self.is_friendly(self.get_piece((j,i))):
                        pieces += [(j,i)]
                
        return pieces


    def is_checkmate(self, pos): # pos is position of the king
        # positions = [(0,0), (1,0), (0,1), (-1,0), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)] # check that all the places the king can move are not safe (use king_move)
        # for dir in positions:
        #     added = self.add_points(dir,pos)
        #     if abs(dir[0]) < 8 and abs(dir[1]) < 8:
        #         test = self.king_move(pos,pos)
        #         if test[0] == True:
        #             return False
        # none of the positions that the king can move to / stay in are safe
        # so now we have to deal with blocking check...
        # we should brute force it by trying to move every piece we have to every location on the board. (dont have to bother with ranges then (max 1024 loops not too bad))

        # first collect all of the pieces we have
        pieces = self.get_current_player_pieces()
        # get the position of the king
        king = self.get_current_player_pieces(target = 4 if self.turn else 10)

        if self.is_safe(king): # check if its safe where it is
            return False

        for piece in pieces:
            for i in range(len(self.board)):
                for j in range(len(self.board[i])):
                    if self.make_move("oof", None, move_tuple = (piece, (j,i)), send = False)[0]:
                        if self.is_safe(king):
                            self.undo_move()
                            return False
                    self.undo_move()
        return True

    def validate_point(self, cord):
        return (cord[0] > -1 and cord[0] < 8)

    def player_in(self, id):
        return str(id) in self.p_ids

    def to_json(self):
        out = {
            "board":self.board,
            "names":self.names,
            "number":self.number,
            "offset":self.offset,
            "players":self.p_ids,
            "size":self.size,
            "stage_path":self.stage_path,
            "turn":self.turn,
            "turn_num":self.turn_num
        }
        return json.dumps(out)

    def from_json(self,json):
        self.board = json["board"]
        self.names = json["names"]
        self.number = json["number"]
        self.offset = json["offset"]
        self.p_ids = json["players"]
        self.size = json["size"]
        self.stage_path = json["stage_path"]
        self.turn = json["turn"]
        self.turn_num = json["turn_num"]
                    

############################
# Type of response methods #
############################

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

#############
# Migration #
#############

def migrate_chat(update):
    try:
        oldchatid = update["message"]["migrate_from_chat_id"] # test for this value
        newchatid = update.message.chat.id
        file = open("data/chat_id.txt")
        file.write(update["message"]["chat"]["id"])
        file.close()
        CHESS_CHAT = get_main_chat()
    except:
        pass

###########################
# Telegram send PIL image #
###########################

def send_photo_from_file(chat_id,image, caption = "oof", reply_id = None, force_reply = False):
    import io
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format='PNG')
    imgByteArr = imgByteArr.getvalue()
    files = {'photo':imgByteArr}
    extra = ''
    if force_reply:
        boi = {"force_reply": True}
        extra = "&reply_markup={}".format(urllib.parse.quote_plus(json.dumps(boi)))
    if reply_id:
        status = requests.post('https://api.telegram.org/bot{}/sendPhoto?chat_id={}&caption={}&reply_to_message_id={}{}'.format(TOKEN, chat_id, caption, reply_id,extra), files=files)
    else:
        status = requests.post('https://api.telegram.org/bot{}/sendPhoto?chat_id={}&caption={}{}'.format(TOKEN, chat_id, caption,extra), files=files)
    file.close()

###########
# Buttons #
###########
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

def gen_ACCEPT(data):
    return {'inline_keyboard': [[{'text' : 'Play', 'callback_data': str(data)}]]}

def gen_ARROWS(start,type):
    return {'inline_keyboard': [[{'text' : '<<', 'callback_data':"move?{}&{}".format(start-10,type)}, {'text' : '>>', 'callback_data':"move?{}&{}".format(start+10,type)}]]}

def gen_LEADEROPTS():
    return {'inline_keyboard': [[{'text' : 'Games Won', 'callback_data':"lgw?"},{'text' : 'Games Lost', 'callback_data':"lgl?"}],
                                [{'text' : 'Turns Taken', 'callback_data':"ltt?"},{'text' : 'Games Played', 'callback_data':"lgp?"}]]}

def send_options(chat_id, options, text, parse_mode = 'HTML', message_id = None):
    text = urllib.parse.quote_plus(text)
    keys = json.dumps(options)
    keys = urllib.parse.quote_plus(keys)
    url = BOT.URL + "sendMessage?text={}&chat_id={}&reply_markup={}&parse_mode={}".format(text,chat_id,keys,parse_mode)
    if message_id:
        url += "&reply_to_message_id={}".format(message_id)
    BOT.get_url(url)

#####################
# Data saving stuff #
#####################
def get_games():
    file = open("data/games.txt", "r")
    data = json.loads(file.read())
    file.close()
    return data

def get_game(game_num):
    try:
        return get_games()[str(game_num)]
    except KeyError as e:
        return None

def add_game(board):
    data = get_games()
    data[board.number] = board.to_json()
    file = open("data/games.txt", "w")
    file.write(json.dumps(data))
    file.close

def remove_game(game_num):
    data = get_games
    data[game_num] = None
    file = open("data/games.txt", "w")
    file.write(json.dumps(data))
    file.close

def increment_game_num():
    num = get_game_num()
    file = open("data/game_count.txt", "w")
    file.write("{}".format(num + 1))
    file.close()

def get_game_num():
    file = open("data/game_count.txt", "r")
    num = int(file.read().strip())
    file.close()
    return num

def get_stats():
    file = open("data/stats.txt")
    data = json.loads(file.read())
    file.close()
    return data

# call after a game is won: info tuple (win bool, turns)
def add_stats(info, user):
    user_id = str(user["id"]) # just in case
    stats = get_stats()
    try:
        stats[user_id]["played"] += 1
        if info[0]:
            stats[user_id]["wins"] += 1
        else:
            stats[user_id]["losses"] += 1
        stats[user_id]["turns"] += info[1]
    except KeyError:
        stats["name"] = get_name()
        stats[user_id]["played"] = 1
        if info[0]:
            stats[user_id]["wins"] += 1
        else:
            stats[user_id]["losses"] += 1
        stats[user_id]["turns"] = info[1]

#####################
# Leaderboard Stuff #
#####################

#keys: "played", "wins", "losses", "turns"
def sort_data_by(data, key):
    pass
    sorted = []
    for stat in data:
        sorted += [(data[stat],data)]
    sorted.sort()
    return sorted

def show_leaderboard(key, start = 0, end = 9):
    data = get_stats()
    translate = {"played": "Games Played", "wins": "Games Won", "losses":"Games Lost", "turns": "Turns Played"}
    data_sorted = sort_data_by(data, key)
    out = "{} Leaderboard! ({}-{})\n".format(translate[key],start+1,end+1)
    for item in data_sorted:
        if start == end:
            break
        out +="{}:\t{} {}\n".format(item[1]["name"], item[1][keys], translate[key].lower())
        start+=1
    return out

#########################
# Button Response Stuff #
#########################

def buttons(update):
    message = update["callback_query"]["message"]
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    accept_user = update['callback_query']["from"]
    data = update['callback_query']["data"]
    if "N?" in data: # make a new game
        data = data.replace("c?","").split(",")
        request_id = data[0]
        game_id = data[1]
        request_name = message["text"].replace(" wants to play a game of chess!", "")
        if not test_dms(accept_user["id"], text= "You've accepted {}'s game request!".format(request_name)):
            # out = BOT.send_message("{} has accepted your game request.".format(accept_user), request_id)
            BOT.send_message("@{}, you need to dm the bot (@DabneyChessBot) before you can play. (it needs dm privilage)".format(get_user_name(accept_user)),chat_id)
            return
        if request_id != str(accept_user["id"]) or request_id == "569239019": # last statement so I can test
            BOT.delete_message(message["message_id"], chat_id)
            BOT.send_message("{} accepted the request from {}!\nSpectate the game with /viewgames".format(get_name(accept_user), request_name), chat_id)
            game = create_game(message, (request_id, accept_user["id"]), (request_name, get_name(accept_user)))
            game.send_board(accept_user["id"])
            add_game(game)
    elif "lgw" in data: # games won leaderboard   
        send_options(chat_id, gen_ARROWS(0,"wins"), show_leaderboard("wins"))
    elif "lgl" in data: # games lost leaderboard
        send_options(chat_id, gen_ARROWS(0,"losses"), show_leaderboard("losses"))
    elif "lgp" in data: # games played leaderboard
        send_options(chat_id, gen_ARROWS(0,"played"), show_leaderboard("played"))     
    elif "ltt" in data: # turns taken leaderboard
        send_options(chat_id, gen_ARROWS(0,"turns"), show_leaderboard("turns"))     
    elif "move?" in data:
        data = data.replace("move?","").split("&")
        data[0] = int(data[0])
        player_num = len(get_stats())
        if data[0] < 0 or data[0] >= player_num:
            return
        if data[0] + 10 >  player_num:
            data[0] += data[0] - player_num
        BOT.delete_message(update['callback_query']["message"]["message_id"], chat_id)
        send_options(chat_id, gen_ARROWS(data[0], data[1]), show_leaderboard(data[1], start = data[0], end = data[0] + 10))

#######################
# BOT Command Methods #
#######################

def message_response(update):
    message = update["message"]
    text = message['text']
    user_id = message["from"]["id"]
    chat_id = message["chat"]["id"]
    name = get_name(message["from"])
    # puts a request for making a new game in to the main chess chat (id in chat_id.txt)
    if "/newgame" in text:
        if not test_dms(user_id, text= "The game request has been sent in!"):
            BOT.send_message("@{}, you need to dm the bot (@DabneyChessBot) before you can play. (it needs dm privilage)".format(get_user_name(message["from"])),chat_id)
            return
        send_options(CHESS_CHAT, gen_ACCEPT("{},{}N?".format(user_id, get_game_num())), "{} wants to play a game of chess!".format(name))
    # sends in the leaderboard buttons if no thing is specified, or presents the leaderboard given
    elif "/leaderboard" in text:
        keys =["played", "wins", "losses", "turns"]
        type = ""
        for key in keys:
            if key in text:
                type = key
                break
        if type:
            send_options(chat_id, gen_ARROWS(0,type), show_leaderboard(type))
        else:
            send_options(chat_id, gen_LEADEROPTS(),"Please select which leaderboard you want to view!",message_id = message["message_id"])
    # view games currently going on
    elif "/viewgames" in text:
        BOT.send_message("This does nothing right now gottem", chat_id)
    # help message
    elif "/help" in text:
        BOT.send_message(help_message, chat_id)
    # move processing
    elif " to " in text and len (text) == 8: # this is a move
        if update["message"]["from"]["id"] != update["message"]["chat"]["id"]:
            BOT.send_message("You can only play the game in dms with the bot",chat_id)
            return
        game_num = get_num_from_image(update)
        if game_num == -1:
            BOT.send_message("Please make sure to reply to the game picture to take your move.\nThanks and enjoy the game!", user_id)
            return
        game_data = get_game(game_num)
        game_to_move = None
        if game_data:
            game_to_move = ChessBoard(None, None, json = json.loads(game_data))
            if game_to_move.process_move(text, user_id):
                add_game(game_to_move) # updates the dictionary that holds all of the games
        else:
            BOT.send_message("This game (#{}) appears to be completed already.\n...or my code is just bad.".format(game_num), user_id)
            return
    else:
        pass

def test_dms(dm_id, text = "Sliding into those dms."):
    result = BOT.send_message(text, dm_id)
    try:
        return result["ok"]
    except Exception as e:
        print(e)
        return False

###############
# Game Making #
###############

# the one who creates the game will be black, and thus move second
def create_game(message, ids, names):
    test = ChessBoard(ids, names)
    return test


def process(update):
    if is_button_response(update):
        buttons(update)
    elif is_message_with_text(update):
        message_response(update)

test = False
# test = True

def main():
    last_update_id = None
    while True:
        updates = BOT.get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = BOT.get_last_update_id(updates) + 1
            for update in updates["result"]:
                migrate_chat(update)
                if test:
                    try:
                        process(update)
                    except Exception as e:
                        pass
                else:
                    process(update)
        time.sleep(0.5)

if __name__ == '__main__':
    main()


# CHECKMATE LOGIC:

# public boolean checkmated(Player player) {
#   if (!player.getKing().inCheck() || player.isStalemated()) {
#       return false; //not checkmate if we are not 
#                     //in check at all or we are stalemated.
#   }

#   //therefore if we get here on out, we are currently in check...

#   Pieces myPieces = player.getPieces();

#   for (Piece each : myPieces) {

#       each.doMove(); //modify the state of the board

#       if (!player.getKing().inCheck()) { //now we can check the modified board
#           each.undoMove(); //undo, we dont want to change the board
#           return false;
#           //not checkmate, we can make a move, 
#           //that results in our escape from checkmate.
#       }

#       each.undoMove();

#   }
#   return true; 
#   //all pieces have been examined and none can make a move and we have       
#   //confimred earlier that we have been previously checked by the opponent
#   //and that we are not in stalemate.
# }