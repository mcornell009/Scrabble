#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import sys
import colorama
from colorama import Fore as FG
from colorama import Back as BG
import random
import enchant
import subprocess
import filter_input

class ScrabbleError(Exception):
    pass

class Word(object):
    """
        wrapper for a word and it's coords
        a word is never outright init'ed, it's always recursively appended to other word objects, until a lump sum is returned
    """
    def __init__(self,x,y,char):
        self.has_wild=False
        if char == "*":
            self.word_str = getWildCard(self.has_wild) #todo make has_wild a Word field, pass it that way, not globally
            self.has_wild=True
            self.pts = 0
        else:
            self.word_str = char
            self.pts = getTileValue(char)
        self.x = x
        self.y = y
        self.word_multi = 1

        multiplier, multi_context = getTileModifier(x,y, context="points")
        print multiplier, multi_context
        if multi_context == "word":
            print "got a word multi!"
            self.word_multi = multiplier
        elif multi_context == "ltr":
            print "got a letter bonus!"
            self.pts *= multiplier


    def append(self,word): # fuck should have overloaded __add__
        print "OTHER",word.word_multi

        self.word_str += word.word_str
        self.pts += word.pts
        self.word_multi *= word.word_multi
        return self

    def is_valid(self):
        return SCRABBLE_DICT.check(self.word_str)

    def __str__(self):
        return self.word_str

    def __repr__(self):
        return self.word_str +":"+ str(self.pts*self.word_multi)
    

class Tile(object):

    def __init__(self,char):
        self.char=char
        if char == "*":
            self.is_wild=True
        else:
            self.is_wild = False
        self.points=getTileValue(char)

    def __repr__(self):
        return self.char+":"+str(self.points)

    def __str__(self):
        return self.char

    def __eq__(self,other):
        return isinstance(other,Tile) and self.char == other.char

    def toString(self):
        return self.char+self.tinyPts()

    def tinyPts(self):
        if self.points == 10:
            return unichr(0x2081) + unichr(0x2080) # 10
        else:
            return unichr(0x2080+self.points)+" " # 0 - 9 subscript, see "SUB"

class Player(object):
    def __init__(self,name):
        self.name = name
        self.score = 0
        self.rack=list()

    def __repr__(self):
        return self.name+":"+str(self.score)

    def __str__(self):
        return self.name+":"+str(self.score)

    def printRack(self):
        rackSize=len(self.rack)
        sys.stdout.write(BOX_TOP_LEFT_CORNER+((BOX_HORIZ*3+BOX_TOP_T)*(rackSize-1))+BOX_HORIZ*3+BOX_TOP_RIGHT_CORNER+'\n')
        for tile in self.rack:
            sys.stdout.write(BOX_VERT+tile.toString())
        sys.stdout.write(BOX_VERT+'\n')
        sys.stdout.write(BOX_BOT_LEFT_CORNER+((BOX_HORIZ*3+BOX_BOT_T)*(rackSize-1))+BOX_HORIZ*3+BOX_BOT_RIGHT_CORNER+'\n')

    def sortRack(self,order=None):
        if order == None:
            random.shuffle(rack)
        else:
            new_rack=list()
            for char in order:
                t = Tile(char)
                if t in self.rack:
                    new_rack.append(t)
                else:
                    print "You can't reorganize tiles you don't have."
                    return
            self.rack = new_rack
            self.printRack()

    def rackString(self):
        ret = ""
        for tile in self.rack:
            ret += tile.char
        return ret

    def hasTiles(self,word):
        temp_rack = self.rackString()
        for word_char in word:
            if word_char in temp_rack:
                temp_rack.replace(word_char,"",1) #take the tile out of your rack, so as to not double count it
            else:
                return False
        return True

BOARD_SIZE=15
board=[[None for x in xrange(BOARD_SIZE)] for x in xrange(BOARD_SIZE)] # 2d array of [BOARD_SIZE][BOARD_SIZE] inited to a string of " "
SCRABBLE_DICT = None # the dict
SAY_PROC = None #global so we can async turn it on and off

BOX_HORIZ=u'─'
BOX_VERT=u'│'
BOX_BOT_LEFT_CORNER=u'└'
BOX_BOT_RIGHT_CORNER=u'┘'
BOX_TOP_LEFT_CORNER=u'┌'
BOX_TOP_RIGHT_CORNER=u'┐'
BOX_TOP_T=u'┬'
BOX_LEFT_T=u'├'
BOX_RIGHT_T=u'┤'
BOX_BOT_T=u'┴'
BOX_CROSS=u'┼'

GRID_CHARS="    A   B   C   D   E   F   G   H   I   J   K   L   M   N   O \n"
TOP_ROW=GRID_CHARS+"  "+BOX_TOP_LEFT_CORNER+(BOX_HORIZ*3+BOX_TOP_T)*(BOARD_SIZE-1)+BOX_HORIZ*3+BOX_TOP_RIGHT_CORNER+'\n'
BOT_ROW="  "+BOX_BOT_LEFT_CORNER+(BOX_HORIZ*3+BOX_BOT_T)*(BOARD_SIZE-1)+BOX_HORIZ*3+BOX_BOT_RIGHT_CORNER+'\n'
MID_ROW="  "+BOX_LEFT_T+(BOX_HORIZ*3+BOX_CROSS)*(BOARD_SIZE-1)+BOX_HORIZ*3+BOX_RIGHT_T+'\n'

TILE_COLOR = FG.BLACK+BG.YELLOW+colorama.Style.BRIGHT
TRIP_WORD_COLOR = FG.BLACK+BG.RED
DOUB_WORD_COLOR = FG.BLACK+BG.MAGENTA
TRIP_LTR_COLOR = FG.BLACK+BG.GREEN
DOUB_LTR_COLOR = FG.BLACK+BG.CYAN

def color(string):
    return string+colorama.Style.RESET_ALL


def getWildCard(is_second):
    wild_counter = color(FG.GREEN+"first")
    if is_second:
        wild_counter = color(FG.GREEN+"second")
    else:
        global SECND_WILD
        SECND_WILD = True
    while True:
        char = raw_input("Enter the char what the "+wild_counter+" wildcard will be:").upper()
        if char.isalnum():
            return char
        else:
            print "That's not a letter."
            continue

def getTileValue(char):
    char = char.lower()
    if char == "*":
        return 0
    elif char=="a" or char=="e" or char=="i" or char=="l" or char=="n" or char=="o"  or char=="r"  or char=="s"  or char=="t"  or char=="u":
        return 1
    elif  char == "d" or char == "g":
        return 2
    elif  char == "b" or char == "c" or char == "m" or char == "p":
        return 3
    elif  char == "f" or char == "h" or char == "v" or char == "w" or char == "y":
        return 4
    elif char == "k":
        return 5
    elif char == "j" or char == "x":
        return 8
    elif char == "q" or char == "z":
        return 10
    else:
        raise ScrabbleError("Tried to get a value for an unrecognized tile.") #this should never happen


def getTileModifier(x,y,context="points"):

    """
    get the special conditions for a given x,y on the board.
    returns values based on context, or a tuple of multiple contexts
    valid contexts are 
                multiplier - the int muliplier of said tile
                mod_type - whether the multiplier is for the letter or the whole word
                bgcolor - the bg color for the tile
                points  - values relevant to scoring (multiplier, mod_type)
                all - all (multiplier, mod_type, bgcolor)
    """
    ret = (1,None,"") # default

    if x == 0 or x == 14:
        if y == 0 or y == 7 or y == 14:
            ret = (3,"word",TRIP_WORD_COLOR)
        elif y == 3 or y == 11:
            ret = (2,"ltr",DOUB_LTR_COLOR)

    elif x == 1 or x == 13:
        if y == 1 or y == 13:
            ret = (2,"word",DOUB_WORD_COLOR)
        elif y == 5 or y == 9:
            ret = (3,"ltr",TRIP_LTR_COLOR)

    elif x == 2 or x == 12:
        if y == 2 or y == 12:
            ret = (2,"word",DOUB_WORD_COLOR)
        elif y == 6 or y == 8:
            ret = (2,"ltr",DOUB_LTR_COLOR)

    elif x == 3 or x == 11:
        if y == 3 or y == 11:
            ret = (2,"word",DOUB_WORD_COLOR)
        elif y == 0 or y == 7 or y == 14:
            ret = (2,"ltr",DOUB_LTR_COLOR)

    elif x == 4 or x == 10:
        if y == 4 or y == 10:
            ret = (2,"word",DOUB_WORD_COLOR)

    elif x == 5 or x == 9:
        if y == 1 or y == 5 or y == 9 or y == 13:
            ret = (3,"ltr",TRIP_LTR_COLOR)

    elif x == 6 or x == 8:
        if y == 2 or y == 6 or y == 8 or y == 12:
            ret = (2,"ltr",DOUB_LTR_COLOR)

    elif x == 7:
        if y == 0 or y == 14:
            ret = (3,"word",TRIP_WORD_COLOR)
        elif y == 3 or y == 11:
            ret = (2,"ltr",DOUB_LTR_COLOR)
        elif y == 7:
            ret = (2,"word",DOUB_WORD_COLOR)
    else:
        raise ScrabbleError("Impossible Tile!")
        
    if context == "muliplier":
        return ret[0]
    elif context == "mod_type":
        return ret[1]
    elif context == "points":
        return (ret[0],ret[1])
    elif context == "bgcolor":
        return ret[2]
    elif context == "all":
        return ret
    else:
        raise ScrabbleError("Invalid context in getTileModifier")

def concat(x,y):
    w = Word(x)
    return w.append(y)

def refillTileBag():
    tileBag=list()

    tileBag.append(Tile("Z"))
    tileBag.append(Tile("Q"))
    tileBag.append(Tile("J"))
    tileBag.append(Tile("K"))
    tileBag.append(Tile("X"))

    for x in xrange(2):
        tileBag.append(Tile("V"))
        tileBag.append(Tile("W"))
        tileBag.append(Tile("Y"))
        tileBag.append(Tile("F"))
        tileBag.append(Tile("H"))
        tileBag.append(Tile("M"))
        tileBag.append(Tile("P"))
        tileBag.append(Tile("B"))
        tileBag.append(Tile("C"))
        tileBag.append(Tile("*"))

    for x in xrange(3):
        tileBag.append(Tile("G"))
    for x in xrange(4):
        tileBag.append(Tile("D"))
        tileBag.append(Tile("L"))
        tileBag.append(Tile("S"))
        tileBag.append(Tile("U"))

    for x in xrange(6):
        tileBag.append(Tile("R"))
        tileBag.append(Tile("T"))
        tileBag.append(Tile("R"))

    for x in xrange(8):
        tileBag.append(Tile("O"))

    for x in xrange(9):
        tileBag.append(Tile("A"))
        tileBag.append(Tile("I"))

    for x in xrange(12):
        tileBag.append(Tile("E"))

    random.shuffle(tileBag)
    return tileBag

def gridCharToInt(char):
    """
        A-O -> 0-14
    """
    return int(char,36)-10

def printBoard():
    sys.stdout.write(TOP_ROW)
    for y in xrange(BOARD_SIZE):
        if y < 9: 
            yStr = str(y+1)+" "
        else:
            yStr = str(y+1)
        sys.stdout.write(yStr)
        for x in xrange(BOARD_SIZE): # english reading format (l->r, then down)
            tile = board[x][y]
            if tile != None:
                sys.stdout.write(BOX_VERT+color(TILE_COLOR+tile.toString()))
            else:
                sys.stdout.write(BOX_VERT+color(getTileModifier(x,y,context="bgcolor")+" "*3))
        sys.stdout.write(BOX_VERT+'\n')
        if y == BOARD_SIZE-1:
            sys.stdout.write(BOT_ROW)
        else:    
            sys.stdout.write(MID_ROW)

def clearBoard():
    for x in xrange(BOARD_SIZE):
        for y in xrange(BOARD_SIZE):
            board[x][y]=None

def pickTiles(players,tileBag): #each player draws one round robin, just like in the rules
    for x in xrange(7):
        for player in players:
            player.rack.append(tileBag.pop())

def wannaQuit():
    yes_or_no=raw_input("Are you sure you want to quit? y/n: ").upper()
    if yes_or_no == "YES" or yes_or_no == "Y":
        print "LOSER"

        sys.exit()

def wannaPass():
    yes_or_no=raw_input("Are you sure you want to pass? y/n: ").upper()
    if yes_or_no == "YES" or yes_or_no == "Y":
        return True
    else:
        return False

def spider(coord_list, across_or_down): 
    """
        recursive search from words
    """
    word_list = list()
    last_coord = coord_list[-1]
    if across_or_down == "A":
        for coord_set in coord_list:
            spiderUp(coord_set[0],coord_set[1],word_list)
        spiderLeft(last_coord[0],last_coord[1],word_list)
    else: #DOWN
        for coord_set in coord_list:
            spiderLeft(coord_set[0],coord_set[1],word_list)
        spiderUp(last_coord[0],last_coord[1],word_list)
    return word_list


def spiderLeft(x,y,wordlist):
    if x == 0 or board[x-1][y] == None:
        word = spiderBackRight(x,y) #word object
        if len(word.word_str) > 1:
            wordlist.append(word)
    else:
        spiderLeft(x-1,y,wordlist)

def spiderUp(x,y,wordlist):
    if y == 0 or board[x][y-1] == None:
        word = spiderBackDown(x,y) #word object
        if len(word.word_str) > 1:
            wordlist.append(word)
    else:
        spiderUp(x,y-1,wordlist)

def spiderBackRight(x,y):
    if x == 15 or board[x+1][y] == None:
        return Word(x,y,board[x][y].char)
    else:
        return Word(x,y,board[x][y].char).append(spiderBackRight(x+1,y))

def spiderBackDown(x,y):
    if y == 15 or board[x][y+1] == None:
        return Word(x,y,board[x][y].char)
    else:
        return Word(x,y,board[x][y].char).append(spiderBackDown(x,y+1))


def checkWords(x,y,across_or_down,word,first_move):
    """
        for each x,y you place, spider horiz + vertically to find all the words. Word scores are calculated tile by tile.
        returns (score,placed_tiles) for the move or False,False for failure 
    """
    print "checking all crosswords..."
    tile_coords=list() # tiles in the word you placed (includes tiles you're connecting to)
    placed_tile_coords=list() # tiles you personally placed (excludes tiles you're connecting to)
    x2 = x
    y2 = y
    word_size = len(word)-1
    if across_or_down == "A":
        x2 = x + word_size
    else:
        y2 = y + word_size

    char_counter = 0
    did_append_to_existing_word=False
    for x_index in xrange(x,x2+1):
        for y_index in xrange(y,y2+1):
            if board[x_index][y_index] == None:
                tile_coords.append((x_index,y_index))
            else:
                tile_coords.append("pass")
                did_append_to_existing_word=True #using an existing tile

    if not did_append_to_existing_word:
        print "A word played must be attached to another word somehow."
        return False,False

    for new_tile in tile_coords:
        if new_tile == "pass":
            char_counter+=1
            continue
        else:
            board[new_tile[0]][new_tile[1]] = Tile(word[char_counter])
            placed_tile_coords.append(new_tile)
            char_counter += 1

    points=0
    found_words = spider(placed_tile_coords,across_or_down)
    if len(placed_tile_coords) == 7: # you placed your whole rack! bingo! 50pt bonus! you go glen coco!
        points += 50
    print found_words

    for word in found_words:
        if not word.is_valid():
            print word.word_str+" is not a valid scrabble word."
            stripTiles(placed_tile_coords) #take your (temp) tiles back from the board
            return False,False
        else:
            points+=(word.pts*word.word_multi)

    placed_tiles = list() #tiles to remove from yout rack
    for coord in placed_tile_coords:
        placed_tiles.append(board[coord[0]][coord[1]])
    return points,placed_tiles

def getMove(player,first_move=False):
    """
        loop until the player makes a successful move
        once a potentially valid move is inputted, check the validity of the words in checkWords(), which returns
        either false or the points for a successful play
    """
    while True:       
        move = raw_input("MAKE YOUR MOVE: ").upper()

        # handle special commands
        if move == "QUIT" or move == "Q":
            wannaQuit()
            continue
        elif move == "QUIT!" or move == "Q!":
            if SAY_PROC:
                SAY_PROC.terminate()
            sys.exit()
            continue
        elif move == "HELP" or move == "H":
            help()
            continue
        elif move == "HELP!" or move == "H!":
            say(helpString())
            continue
        elif move == "SHUTUP!" or move == "S!":
            shutUp(fuck=True)
            continue
        elif move == "SHUTUP" or move == "S":
            shutUp()
            continue
        elif move == "BOARD" or move == "B":
            printBoard()
            continue
        elif move == "CLEAR" or move == "C": 
            clearTerminal()
            printBoard()
            continue
        elif move == "CLEAR!" or move == "C!": # TODO board -> clear, you end up with a half drawn new board. clear again fixes this
            clearTerminalAndBuffer()
            printBoard()
            continue
        elif move == "PASS" or move == "P": 
            if wannaPass():
                break
            else:
                continue
        elif move == "PASS!" or move == "P!": 
            break
        
        # mostly used to catch blank lines or me typing ASFADS like an asshole
        if len(move) < 7:
            print "That's too short to be a command."
            continue

        parts=move.split(":")
        if len(parts) != 3:
            print "Can't find all the parts of the move command. Maybe you're missing/have too many \":\"?"
            continue

        for item in parts:
            if len(item) == 0:
                print "Found a blank command. Maybe you left in an extra \":\"?"
                continue

        coords = parts[0].replace(" ","") # incase of space inbetween file and rank
        direction = parts[1].strip()
        word = parts[2].strip()

        if not coords[0].isalpha():
            print "I don't know where to put your word (Bad file coord)."
            continue

        if not coords[1:].isdigit():
            print "I don't know where to put your word (Bad rank coord)."
            continue

        x = gridCharToInt(coords[0])
        y = int(coords[1:]) - 1
        if 14 < x < 0 or 14 < y < 0:
            print "Those aren't coords on the board. Valid Files are from A-O, valid Ranks are 1-15."
            continue

        if first_move:
            if x != 7 or y != 7:
                print "The first move must start from the center (H8)."
                continue

        #compact that command
        if direction == "ACROSS":
            direction = "A"
        elif direction == "DOWN":
            direction = "D"
        if direction != "A" and direction !="D":
            print "I don't know where to put your word (Across or Down?)."
            continue
        
        score,placed_tiles = checkWords(x,y,direction,word,first_move)
        if not score: #error reporting is handling in check words
            continue
        else:
            for tile in placed_tiles:
                if not tile in player.rack:
                    print "You don't have the tiles to play that!"
                    continue
                    player.rack.remove(tile)
            print player.name+" scored "+str(score)+" on that last play!"
            player.score+=score
            for tile in placed_tiles:
                player.rack.remove(tile)
            break #YAY

def stripTiles(coord_list):
    for coord in coord_list:
        board[coord[0]][coord[1]] = None

def printScores(players):
    for player in players:
        print color(FG.CYAN+player.name) +" has " + color(FG.GREEN+str(player.score))+" points."

def initGame():   
    clearBoard()
    tileBag = refillTileBag()
    players=list() # empty
    player_counter = 1
    name = raw_input("Enter Player "+str(player_counter)+"'s name: ").upper()
    while True: #TODO this could easily be a for loop
        if len(name) > 0:
            players.append(Player(name))
            if len(players)==2:
                break #YAY
            player_counter+=1
        else:
           continue
        name = raw_input("Enter Player "+str(player_counter)+"'s name: ").upper()
    pickTiles(players,tileBag)
    print "" #clean up init from gameplay
    return (players,tileBag)
    
def gameLoop(players,tileBag):
    first_move=True
    while True:
        for player in players:
            # clearTerminalBuffer() TODO should I even use this thing? bluh
            printScores(players)
            printBoard()

            print "It's "+color(FG.GREEN+player.name)+"'s turn."
            player.printRack()
            getMove(player,first_move=first_move) #do all the turn logic
            if first_move:
                first_move = False
            while len(player.rack)<7:
                newTile=tileBag.pop()
                print player.name +" drew : "+color(FG.GREEN+newTile.char)
                player.rack.append(newTile)
def help():
    print color(TRIP_WORD_COLOR + "3x WORD") + " " + color(DOUB_WORD_COLOR + "2x WORD")
    print color(TRIP_LTR_COLOR + "3x  LTR") + " " + color(DOUB_LTR_COLOR + "2x  LTR")+"\n" # extra spaces for justification
    print "Move formatting:"+color(FG.YELLOW+"<file>"+FG.RED+"<rank>")+":"+color(FG.BLUE+"<(D)own or (A)cross>")+":"+color(FG.GREEN+"WORD")+"."
    print "All move formatting is case-insensitive. -->", #-------------------------------------------all
    print color(FG.YELLOW+"h"+FG.RED+"8")+":"+color(FG.BLUE+"d")+":"+color(FG.GREEN+"word"), #-----------one 
    print "OR "+color(FG.YELLOW+"H"+FG.RED+"8")+":"+color(FG.BLUE+"DOWN")+":"+color(FG.GREEN+"WORD") #-----line
    print "The File and Rank of a word must be where the first letter of the word appears, not where the first tile you place is."
    print "Type "+color(FG.GREEN+"(H)ELP")+" to see this message at any time, append a ! to hear it."
    print "Type "+color(TILE_COLOR+"(S)HUTUP")+" to cease your foolish mistake of listening to the help message, append a ! to really mean it."
    print "Type "+color(FG.RED+"(Q)UIT")+" to quit the game, append a ! to force quit."
    print "Type "+color(FG.BLUE+"(B)OARD")+" to reexamine the board, append a ! to be really excited about it."
    print "Type "+color(FG.MAGENTA+"(P)ASS")+" to skip your turn, append a ! skip confirmation."
    print "Type "+color(FG.YELLOW+"(C)LEAR")+" to clear the terminal and reexamine the board, append a ! to clear the buffer entirely."

def helpString():
    hstr = """ Red is triple word. Magenta is double word. Green is triple letter. Blue is double letter. Move formatting is file, 
    rank, colon, down or across, colon, word. All move formatting is case-insensitive. The File and Rank of a word 
    must be where the first letter of the word appears, not where the first tile you place is. 
    Type help to see this message at any time, append a bang to hear it. 
    Type shutup to cease your foolish mistake of listening to the help message, append a bang to really mean it. 
    Type quit to quit the game, append a bang to force quit. 
    Type board to reexamine the board, append a bang to be really excited about it. 
    Type pass to skip your turn, append a bang skip confirmation. 
    Type clear to clear the terminal and reexamine the board, append a bang to clear the buffer entirely. """
    return hstr
            
def banner():
    print color(FG.CYAN+"~~~~SCRABBLE-ISH~~~~")
    print color(FG.CYAN+"~~sleepygarden '13~~")

def clearTerminalAndBuffer(): #as opposed to clear (which lets you scroll up to your opponents rack)
    subprocess.call(["osascript", "clear_terminal_buffer.applescript"])

def clearTerminal(): #as opposed to clear (which lets you scroll up to your opponents rack)
    subprocess.call(["clear"])

def say(phrase): #for the luls
    global SAY_PROC
    SAY_PROC = subprocess.Popen(["say"]+[phrase])

def shutUp(fuck=False):
    if SAY_PROC:
        SAY_PROC.terminate()
    if fuck:
        subprocess.call(["say","-v","Bad News","shut up!"])

def main():
    #clearTerminalAndBuffer()
    colorama.init()
    banner()
    print "Loading Scrabble Dictionary (TWL)..."
    global SCRABBLE_DICT
    SCRABBLE_DICT = enchant.request_pwl_dict("cleaned_TWL.txt") #tournament word list
    help()
    filter_input.bufferHistory() #not using this anymore
    while True:
        players, tileBag = initGame()
        gameLoop(players,tileBag)

if __name__ == "__main__":
    main()

