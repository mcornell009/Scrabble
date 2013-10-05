#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import sys
import colorama
import random
import enchant

class ScrabbleError(Exception):
    pass

class Tile(object):

    def __init__(self,char):
        self.char=char
        self.points=getTileValue(char)

    def __repr__(self):
        return self.char+":"+str(self.points)

    def __str__(self):
        return self.char

    def toString(self):
        return self.char+self.tinyPts()

    def tinyPts(self):
        if self.points == 10:
            return SUB_ONE+SUB_ZERO
        else:
            return unichr(0x2080+self.points)+" " # 0 - 9 subscript, see "SUB"

    def _getTileValue(self):
        return 0

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
                if t is in self.rack:
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

TILE_COLOR = colorama.Fore.BLACK+colorama.Back.YELLOW+colorama.Style.BRIGHT
TRIP_WORD_COLOR = colorama.Fore.BLACK+colorama.Back.RED+colorama.Style.NORMAL
DOUB_WORD_COLOR = colorama.Fore.BLACK+colorama.Back.MAGENTA+colorama.Style.NORMAL
TRIP_LTR_COLOR = colorama.Fore.BLACK+colorama.Back.GREEN+colorama.Style.NORMAL
DOUB_LTR_COLOR = colorama.Fore.BLACK+colorama.Back.CYAN+colorama.Style.NORMAL
RESET = colorama.Style.RESET_ALL

def getTileValue(char):
    char = char.lower()
    if char == " ":
        return 0
    elif char == "a" or char == "e" or char == "i" or char == "l" or char == "n" or char == "o"  or char == "r"  or char == "s"  or char == "t"  or char == "u":
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
        tileBag.append(Tile(" "))

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
                sys.stdout.write(BOX_VERT+color(Tile.color+tile.toString()))
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
    if yes_or_no == "yes" or yes_or_no == "y" or yes_or_no == "Y" or yes_or_no == "Yes" or yes_or_no == "YES":
        print "LOSER"
        sys.exit()

"""
    for each x,y you place, spider left and up until you hit a empty space or 0 index.
    from that x,y, spider in the reverse of the direction you came from (left -> right, up -> down) until you hit an empty space or 15 
    index, collecting letters into a word. add the complete word to a list. once all spidering finishes, for each word, validate and score
    also check from each placed tile is touching another in any direction, but not recursively, to establish that you haven't placed a floating word 
"""
def checkWords(x,y,across_or_down,word):
    print "checking all crosswords..."
    placed_tile_coords=list()
    found_words=list()
    x2 = x
    y2 = y
    if across_or_down == "ACROSS" or across_or_down == "A":
        x2 = x + len(word) - 1
    else:
        y2 = y + len(word) - 1

    print str(x)+"->"+str(x2)+","+str(y)+"->"+str(y2)
    for x_index in xrange(x,x2):
        for y_index in xrange(y,y2):
            if board[x][y] == None:
                print "got a tile place"
                placed_tile_coords.append(x,y) # hold these in an array before place, in case of bad words
    counter = 0
    for new_tile in placed_tile_coords:
        board[new_tile[0]][new_tile[1]] = Tile(word[counter])

def getMove():
    while True:       
        move = raw_input("MAKE YOUR MOVE: ")
        if move == "quit":
            wannaQuit()
            continue

        elif move == "board":
            printBoard()
            continue

        if len(move) < 2:
            print "That's too short. Try something like \"XY down : word\"."
            continue

        parts=move.split(":")
        if len(parts) < 3:
            print "Can't find all the parts of the move command. Maybe you're missing a :? Try something like \"XY : down : word\"."
            continue

        coords = parts[0].strip()
        direction = parts[1].strip().upper()
        word = parts[2].strip().upper()
        x = gridCharToInt(coords[0])
        y = int(coords[1])

        if not coords[0].isalpha() or not coords[1].isdigit():
            print "I don't know where to put your word. (Bad Coords) Try something like \"XY : down : word\"."
            continue

        if not (direction == "ACROSS" or direction == "A" or direction == "DOWN" or direction == "D"):
            print "I don't know where to put your word. (Across or Down) Try something like \"XY : down : word\"."
            continue

        if checkWords(x,y,direction,word): #to save on space, word list is only uppercase
            break # got it!
        else:
            print "\"" + word + "\" isn't a valid Scrabble word."
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
        name = raw_input("Enter Player "+str(counter)+" name: ")
    pickTiles()
    
def gameLoop():
    gameOn=True
    while gameOn:
        for player in players:
            printBoard()
            print "It's "+player.name+"'s turn."
            print player.name+"'s Rack:"
            player.printRack()
            getMove()
            while len(player.rack)<7:
                newTile=tileBag.pop()
                print player.name +" drew a "+newTile.char
                player.rack.append(newTile)
            
def banner():
    print colorama.Fore.CYAN
    print "~~~SCRABBLE-ISH~~~"
    print "~sleepygarden '13~"
    print color(TRIP_WORD_COLOR + "3x WORD") + " " + color(DOUB_WORD_COLOR + "2x WORD")
    print color(TRIP_LTR_COLOR + "3x LTR") + "   " + color(DOUB_LTR_COLOR + "2x LTR")
    print "Move formatting: \"<rank><file> : <(d)own or (a)cross> : word\"."
    print "All move formatting is case-insensitive -> \"a9 down : maze\" or \"A9 D : MAZE\""


def loadTwl():
    print "Loading Scrabble Dictionary (TWL)..."
    global twl
    twl = enchant.request_pwl_dict("cleaned_twl.txt") #tournament word list

def main():
    colorama.init()
    banner()
    loadTwl()
    while True:
        initGame()
        gameLoop()

if __name__ == "__main__":
    main()