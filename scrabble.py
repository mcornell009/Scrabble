#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import sys
import colorama
class Tile(object):
    @staticmethod
    def nil():
        return Tile(" ",-1)

    def __init__(self,char,pts):
        self.char=char
        self.points=pts

    def __repr__(self):
        return self.char+":"+str(self.points)

    def toString(self):
        return self.char+self.tinyPts()

    def tinyPts(self):
        if self.points == 10:
            return SUB_X
        else:
            return unichr(0x2080+self.points) # 0 - 9 subscript, see "SUB"

    def _getTileValue(self):
        return 0

class Player(object):
    def __init__(self,name):
        self.name = name
        self.score = 0
        self.rack=list()
    def __repr__(self):
        return self.name+":"+str(self.score)

    def printRack(self):
        rackSize=len(self.rack)
        sys.stdout.write(BOX_TOP_LEFT_CORNER+((BOX_HORIZ+BOX_HORIZ+BOX_TOP_T)*(rackSize-1))+BOX_HORIZ+BOX_HORIZ+BOX_TOP_RIGHT_CORNER+'\n')
        for tile in self.rack:
            sys.stdout.write(BOX_VERT+tile.toString())
        sys.stdout.write(BOX_VERT+'\n')
        sys.stdout.write(BOX_BOT_LEFT_CORNER+((BOX_HORIZ+BOX_HORIZ+BOX_BOT_T)*(rackSize-1))+BOX_HORIZ+BOX_HORIZ+BOX_BOT_RIGHT_CORNER+'\n')



board_size=15
board=[[" " for x in xrange(board_size)] for x in xrange(board_size)] # 2d array of [board_size][board_size]
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

TOP_ROW=BOX_TOP_LEFT_CORNER+(BOX_HORIZ+BOX_HORIZ+BOX_TOP_T)*(board_size-1)+BOX_HORIZ+BOX_HORIZ+BOX_TOP_RIGHT_CORNER+'\n'
BOT_ROW=BOX_BOT_LEFT_CORNER+(BOX_HORIZ+BOX_HORIZ+BOX_BOT_T)*(board_size-1)+BOX_HORIZ+BOX_HORIZ+BOX_BOT_RIGHT_CORNER+'\n'
MID_ROW=BOX_LEFT_T+(BOX_HORIZ+BOX_HORIZ+BOX_CROSS)*(board_size-1)+BOX_HORIZ+BOX_HORIZ+BOX_RIGHT_T+'\n'

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

def testUnichars():
    domain=0x2080
    for x in xrange(10):
        print unichr(domain+x)
        print unichr(0x2093)


def refillTileBag():
    tileBag[:]=[] # empty
    while len(tileBag) < 102:
        tileBag.append(Tile("A",5))

def printBoard():
    sys.stdout.write(TOP_ROW)
    for y in xrange(board_size):
        for x in xrange(board_size):
            tile = board[x][y]
            if tile != None:
                sys.stdout.write(BOX_VERT+tile.toString())
            else:
                sys.stdout.write(BOX_VERT+"  ")
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
        player.rack.append(Tile("A",5))
        player.rack.append(Tile("A",5))
        player.rack.append(Tile("A",5))
        player.rack.append(Tile("A",5))
        player.rack.append(Tile("A",5))
        player.rack.append(Tile("A",5))

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

def gameLoop():
    gameOn=True
    while gameOn:
        for player in players:
            printBoard()
            print "It's"+player.name+"'s turn."
            print player.name+"'s Rack:"
            player.printRack()
            move = raw_input("MAKE YOUR MOVE: ")

def main():
    while True:
        initGame()
        gameLoop()

if __name__ == "__main__":
    #testUnichars()
    colorama.init()
    main()