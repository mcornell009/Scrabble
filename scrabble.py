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

class Tile(object):

    def __init__(self,char):
        self.char=char
        if char == "*":
            self.is_wild=True
            self.wild_char = "*"
        else:
            self.is_wild = False
        self.points=getTileValue(char)

    def __repr__(self):
        return self.char+":"+str(self.points)

    def __str__(self):
        return self.char

    def setWildChar(self,char):
        if self.is_wild:
            self.wild_char=char
        else:
            raise ScrabbleError("You can't use any old tile as a wildcard dummy.")

    def toString(self):
        if self.is_wild:
            return self.wild_char+SUB_ZERO
        else:
            return self.char+self.tinyPts()

    def tinyPts(self):
        if self.points == 10:
            return SUB_ONE+SUB_ZERO
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




board_size=15
board=[[" " for x in xrange(board_size)] for x in xrange(board_size)] # 2d array of [board_size][board_size] inited to a string of " "
players=list()
tileBag=list()
twl = None

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
TOP_ROW=GRID_CHARS+"  "+BOX_TOP_LEFT_CORNER+(BOX_HORIZ*3+BOX_TOP_T)*(board_size-1)+BOX_HORIZ*3+BOX_TOP_RIGHT_CORNER+'\n'
BOT_ROW="  "+BOX_BOT_LEFT_CORNER+(BOX_HORIZ*3+BOX_BOT_T)*(board_size-1)+BOX_HORIZ*3+BOX_BOT_RIGHT_CORNER+'\n'
MID_ROW="  "+BOX_LEFT_T+(BOX_HORIZ*3+BOX_CROSS)*(board_size-1)+BOX_HORIZ*3+BOX_RIGHT_T+'\n'

SUB_ZERO = u'₀' #lol
SUB_ONE = u'₁'
SUB_TWO = u'₂'
SUB_THREE = u'₃'
SUB_FOUR = u'₄'
SUB_FIVE = u'₅'
SUB_SIX = u'₆'
SUB_SEVEN = u'₇'
SUB_EIGHT = u'₈'
SUB_NINE = u'₉'
SUB_X = u'ₓ' #roman numerals yo

TILE_COLOR = FG.BLACK+BG.YELLOW+colorama.Style.BRIGHT
TRIP_WORD_COLOR = FG.BLACK+BG.RED+colorama.Style.NORMAL
DOUB_WORD_COLOR = FG.BLACK+BG.MAGENTA+colorama.Style.NORMAL
TRIP_LTR_COLOR = FG.BLACK+BG.GREEN+colorama.Style.NORMAL
DOUB_LTR_COLOR = FG.BLACK+BG.CYAN+colorama.Style.NORMAL
RESET = colorama.Style.RESET_ALL

def getTileValue(char):
    char = char.lower()
    if char == " ":
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
        raise ScrabbleError("Tried to get a value for an unrecognized tile.")


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
def getTileModifier(x,y,context="points"):
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

def refillTileBag():
    tileBag[:]=[] # empty

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



def color(string):
    return string+RESET

def intToGridChar(x):
    print "OK"+chr(x+65)+" "
    return chr(x+65)+" "

def gridCharToInt(char):
    return int(char,36)-10

def printBoard():
    sys.stdout.write(TOP_ROW)
    for y in xrange(board_size):
        if y < 9: 
            yStr = str(y+1)+" "
        else:
            yStr = str(y+1)
        sys.stdout.write(yStr)
        for x in xrange(board_size): # english reading format (l->r, then down)
            tile = board[x][y]
            if tile != None:
                sys.stdout.write(BOX_VERT+color(TILE_COLOR+tile.toString()))
            else:
                sys.stdout.write(BOX_VERT+color(getTileModifier(x,y,context="bgcolor")+" "*3))
        sys.stdout.write(BOX_VERT+'\n')
        if y == board_size-1:
            sys.stdout.write(BOT_ROW)
        else:    
            sys.stdout.write(MID_ROW)

def clearBoard():
    for x in xrange(board_size):
        for y in xrange(board_size):
            board[x][y]=None

def pickTiles(): #each player draws one round robin, just like in the rules
    for x in xrange(7):
        for player in players:
            player.rack.append(tileBag.pop())

def wannaQuit():
    yes_or_no=raw_input("Are you sure you want to quit? y/n: ")
    yes_or_no = yes_or_no.upper()
    if yes_or_no == "YES" or yes_or_no == "Y":
        print "LOSER"
        sys.exit()

def spider(coord_list, word_list, across_or_down): 

    if across_or_down == "ACROSS":
        for coord_set in coord_list:
            spiderDown(coord_set[0],coord_set[1],word_list)
        last_coord = coord_list.pop()
        spiderAcross(last_coord[0],last_coord[1],word_list)

    elif across_or_down == "DOWN":
        for coord_set in coord_list:
            spiderAcross(coord_set[0],coord_set[1],word_list)
        last_coord = coord_list.pop()
        spiderDown(last_coord[0],last_coord[1],word_list)
    else:
        raise ScrabbleError("Spider can't go that way (invalid direction).")

def spiderAcross(x,y,wordlist):
    if x == 0 or board[x-1][y] == None:
        word = spiderBackAcross(x,y) #list of Tiles
        if len(word) > 1:
            print "GOT "+word
            wordlist.append(word)
    else:
        spiderAcross(x-1,y,wordlist)
    pass

def spiderDown(x,y,wordlist):
    if y == 0 or board[x][y-1] == None:
        word = spiderBackDown(x,y) #list of Tiles
        if len(word) > 1:
            print "GOT "+word
            wordlist.append(word)
    else:
        spiderDown(x,y-1,wordlist)
    pass

def spiderBackAcross(x,y):
    if x == 15 or board[x+1][y] == None:
        print "back terminal x!"
        return board[x][y].char
    else:
        return board[x][y].char + spiderBackAcross(x+1,y)

def spiderBackDown(x,y):
    if y == 15 or board[x][y+1] == None:
        print "back terminal y"
        return board[x][y].char
    else:
        return board[x][y].char + spiderBackDown(x,y+1)



def checkWords(x,y,across_or_down,word):
    """
        for each x,y you place, spider left and up until you hit a empty space or 0 index.
        from that x,y, spider in the reverse of the direction you came from (left -> right, up -> down) until you hit an empty space or 15 
        index, collecting letters into a word. add the complete word to a list. once all spidering finishes, for each word, validate and score
        also check from each placed tile is touching another in any direction, but not recursively, to establish 
        that you haven't placed a floating word 
    """
    print "checking all crosswords..."
    placed_tile_coords=list()
    to_check_coords=list()
    found_words=list()
    x2 = x
    y2 = y
    if across_or_down == "ACROSS":
        x2 = x + len(word) - 1
    else:
        y2 = y + len(word) - 1

    print str(x)+","+str(y)+"->"+str(x2)+","+str(y2)
    char_counter = 0
    for x_index in xrange(x,x2+1):
        for y_index in xrange(y,y2+1):
            print str(x_index)+","+str(y_index)
            if board[x_index][y_index] == None:
                placed_tile_coords.append((x_index,y_index))
            else:
                placed_tile_coords.append("pass")

    for new_tile in placed_tile_coords:
        if new_tile == "pass":
            char_counter+=1
            continue
        else:
            new_x = new_tile[0]
            new_y = new_tile[1]
            print "placing a tile at "+str(new_x)+","+str(new_y)
            board[new_x][new_y] = Tile(word[char_counter])
            to_check_coords.append(new_tile)
            char_counter += 1


    spider(to_check_coords,found_words,across_or_down) #i know this is functional, and i don't care

    print found_words
    points = 0
    for word in found_words:
        is_valid = twl.check(word)
        if not is_valid:
            return False
        else:
            points += scoreWord(word)
    return points

def stripTiles(coord_list):
    for coord in coord_list:
        if coord == "pass":
            pass
        remove_x = coord[0]
        remove_y = coord[1]
        board[remove_x][remove_y] = None

def getMove():
    while True:       
        move = raw_input("MAKE YOUR MOVE: ")
        move = move.upper()
        if move == "QUIT" or move == "Q":
            wannaQuit()
            continue
        elif move == "QUIT!" or move == "Q!":
            sys.exit()
            continue
        elif move == "HELP" or move == "H":
            help()
            continue
        elif move == "BOARD" or move == "B":
            printBoard()
            continue
        elif move == "CLEAR" or move == "C": # TODO if you enter board then clear, you end up with a half drawn new board. clear again fixes this
            clearTerminalBuffer()
            printBoard()
            continue
        
        if len(move) < 7:
            print "That's too short to be a command."
            continue

        parts=move.split(":")
        if len(parts) != 3:
            print "Can't find all the parts of the move command. Maybe you're missing/have to many \":\"?"
            continue

        for item in parts:
            if len(item) == 0:
                print "Found a null command. Maybe you left in an extra \":\"?"
                continue

        coords = parts[0].strip()
        direction = parts[1].strip()
        word = parts[2].strip()

        x = gridCharToInt(coords[0])
        if not coords[0].isalpha():
            print "I don't know where to put your word (Bad file coord)."
            continue

        y = int(coords[1]) - 1
        if  not coords[1].isdigit():
            print "I don't know where to put your word (Bad rank coord)."
            continue

        if direction == "ACROSS" or direction == "A":
            direction = "ACROSS"
        elif direction == "DOWN" or direction == "D":
            direction = "DOWN"
        else:
            print "I don't know where to put your word (Across or Down?)."
            continue

        if not word.isalnum():
            print "That isn't a word (invalid character)"
            continue

        if checkWords(x,y,direction,word):
            break # got it!
        else:
            print "Couldn't valid your word(s). Try again."
            continue
        

def initGame():   
    clearBoard()
    refillTileBag()
    players[:]=[] # empty
    counter = 1
    name = raw_input("Enter Player "+str(counter)+"'s name: ")
    while len(players)<1:
        if len(name) > 0:
            players.append(Player(name))
            counter+=1
        else:
           continue
        name = raw_input("Enter Player "+str(counter)+"'s name: ")
    pickTiles()
    
def gameLoop():
    gameOn=True
    while gameOn:
        for player in players:
            # clearTerminalBuffer() TODO should I even use this thing?
            printBoard()
            print "It's "+color(FG.GREEN+player.name.upper())+"'s turn."
            player.printRack()
            getMove()
            while len(player.rack)<7:
                newTile=tileBag.pop()
                print player.name +" drew "+color(FG.GREEN+newTile.char)
                player.rack.append(newTile)

def help():
    print color(TRIP_WORD_COLOR + "3x WORD") + " " + color(DOUB_WORD_COLOR + "2x WORD")
    print color(TRIP_LTR_COLOR + "3x  LTR") + " " + color(DOUB_LTR_COLOR + "2x  LTR")
    print color("Move formatting:"+FG.YELLOW+"\"<file>"+FG.RED+"<rank>"+RESET+" : "+FG.BLUE+"<(D)own or (A)cross>"+RESET+" : "+FG.GREEN+"WORD\".")
    
    print "All move formatting is case-insensitive. -->", #all
    print color(FG.YELLOW+"h"+FG.RED+"8"+RESET+":"+FG.BLUE+"d"+RESET+":"+FG.GREEN+"word"), # one 
    print "OR "+color(FG.YELLOW+"H"+FG.RED+"8"+RESET+":"+FG.BLUE+"DOWN"+RESET+":"+FG.GREEN+"WORD") # line

    print "Type "+color(FG.GREEN+"(H)ELP")+" to see this message at any time."
    print "Type "+color(FG.RED+"(Q)UIT")+" to quit the game, append a ! to force quit."
    print "Type "+color(FG.BLUE+"(B)OARD")+" at any time to rexamine the board"
    print "Type "+color(FG.YELLOW+"(C)LEAR")+" at any time to clear the terminal and then rexamine the board"
            
def banner():
    print color(FG.CYAN+"~~~SCRABBLE-ISH~~~")
    print color(FG.CYAN+"~sleepygarden '13~")

def clearTerminalBuffer(): #as opposed to clear (which lets you scroll up to your opponents rack)
    subprocess.call(["osascript", "clear_terminal_buffer.applescript"])
    #sys.stdout.write(RESET)


def main():
    clearTerminalBuffer()
    banner()
    colorama.init()
    print "Loading Scrabble Dictionary (TWL)..."
    global twl
    twl = enchant.request_pwl_dict("cleaned_twl.txt") #tournament word list
    help()
    filter_input.bufferHistory()
    while True:
        initGame()
        gameLoop()

if __name__ == "__main__":
    main()