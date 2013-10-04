#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import sys
import colorama

class ScrabbleError(Exception):
    pass

class Tile(object):

    def __init__(self,char,pts):
        self.char=char
        self.points=pts

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



board_size=15
board=[[" " for x in xrange(board_size)] for x in xrange(board_size)] # 2d array of [board_size][board_size] inited to a string of " "
players=list()
tileBag=list()

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

TOP_ROW=BOX_TOP_LEFT_CORNER+(BOX_HORIZ*3+BOX_TOP_T)*(board_size-1)+BOX_HORIZ*3+BOX_TOP_RIGHT_CORNER+'\n'
BOT_ROW=BOX_BOT_LEFT_CORNER+(BOX_HORIZ*3+BOX_BOT_T)*(board_size-1)+BOX_HORIZ*3+BOX_BOT_RIGHT_CORNER+'\n'
MID_ROW=BOX_LEFT_T+(BOX_HORIZ*3+BOX_CROSS)*(board_size-1)+BOX_HORIZ*3+BOX_RIGHT_T+'\n'

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

TILE_COLOR = colorama.Fore.BLACK+colorama.Back.YELLOW
TRIP_WORD_COLOR = colorama.Fore.BLACK+colorama.Back.RED
DOUB_WORD_COLOR = colorama.Fore.BLACK+colorama.Back.MAGENTA
TRIP_LTR_COLOR = colorama.Fore.BLACK+colorama.Back.GREEN
DOUB_LTR_COLOR = colorama.Fore.BLACK+colorama.Back.CYAN


"""
    UGH THIS THING SUCKS
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
    while len(tileBag) < 102:
        tileBag.append(Tile("A",5))

def color(string):
    return string+colorama.Style.RESET_ALL

def printBoard():
    sys.stdout.write(TOP_ROW)
    for y in xrange(board_size):
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

def pickTiles():
    for player in players:
        player.rack.append(Tile("A",5))
        player.rack.append(Tile("B",5))
        player.rack.append(Tile("C",5))
        player.rack.append(Tile("D",5))
        player.rack.append(Tile("E",5))
        player.rack.append(Tile("F",5))
        player.rack.append(Tile("G",5))

def initGame():   
    clearBoard()
    refillTileBag()
    players[:]=[] # empty
    counter = 1
    name = raw_input("Enter Player "+str(counter)+" name: ")
    while len(players)<2:
        if name.isalnum():
            players.append(Player(name))
        else:
            print "That's a dumb name. Try again."
        counter+=1
        if len(players)==2:
            break
        name = raw_input("Enter Player "+str(counter)+" name: ")
    pickTiles()

def processMove(move): #TODO
    print "MOVE-->"+move
    
def gameLoop():
    gameOn=True
    while gameOn:
        for player in players:
            printBoard()
            print "It's "+player.name+"'s turn."
            print player.name+"'s Rack:"
            player.printRack()
            move = raw_input("MAKE YOUR MOVE: ")
            if move == "quit":
                yes_or_no=raw_input("Are you sure you want to quit? y/n ")
                if yes_or_no == "yes" or "y" or "Y" or "Yes" or "YES":
                    print "LOSER"
                    sys.exit()
            else:
                processMove(move)
def banner():
    print colorama.Fore.CYAN
    print "~~~SCRABBLE-ISH~~~"
    print "~sleepygarden '13~"
    print TRIP_WORD_COLOR + "3x WORD" + colorama.Back.RESET + " " + DOUB_WORD_COLOR + "2x WORD" + colorama.Back.RESET
    print TRIP_LTR_COLOR + "3x LTR" + colorama.Back.RESET + "   " + DOUB_LTR_COLOR + "2x LTR" + colorama.Style.RESET_ALL

def main():
    banner()
    while True:
        initGame()
        gameLoop()

if __name__ == "__main__":
    colorama.init()
    main()