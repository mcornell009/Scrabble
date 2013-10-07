import sys
import collections
from sys import stdout

"""
    filter_inputer.py
    replacement for raw_input, so that way you can ignore stuff like arrow key presses
"""
class FilterInputException(Exception):
    pass

class _Getch: #shout out to the internet for this code
    """
    Gets a single character from standard input.  Does not echo to the
    screen.
    """
    def __init__(self):
        try:
            self.impl = _GetchUnix()
        except ImportError:
            self.impl = _GetchWindows()

    def __call__(self): 
        return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty

    def __call__(self):
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

_PY_INTERRUPT = chr(3)
_EOF = chr(4)
_DELETE = chr(127)
_ESC = chr(27)
_SOH = chr(1)
_BACKSPACE_HACK = "\b"+_DELETE+"\b"
_CURSOR_MOVE_B = "\033[1D"
_RESET_LINE = "\033[K"

_MAX_BUFF_SIZE = 5000
_MAX_HIST_SIZE = 5000
NO_BUFF_LIMIT = -1


_buffer_history=None #stack of entered strings
_popped_history=None #store popped _buffer_history items to put back
_should_buffer_history=False

def getFilteredStr(ignoring_chars_list=list(), message=None,visible=True):
    """
        gets a string from stdin, returns after a newline, 
        ignores any char in the ignoring_chars_list outright (doesn't even check against special cases, like crtl-c and arrow keys)
        does not echo if visible=False
        has default max in size to prevent overflow, but is setable to NO_BUFF_LIMIT (-1)
    """
    if message != None:
        print message,
    string = ""
    original_hist_string=""
    cursor_index=0
    getch = _Getch()
    char = getch()

    while char != '\r':
        if char in ignoring_chars_list:
            char = getch()
            continue
        elif char == _PY_INTERRUPT:
            raise KeyboardInterrupt("Interrupted Filter String")
        elif char == _EOF:
            raise EOFError("Interrupted Filter String")

        if char == _DELETE or char == '\b':
            if len(string) > 0:
                string = string[:-1]
                stdout.write(_BACKSPACE_HACK)
                cursor_index -= 1
                char = getch()
                continue

        elif char == _ESC and _should_buffer_history == True:   # TODO THIS IS A SHIT WAY TO DO THINGS 
            esc_cmd = getch()                                   # I BET YOU'LL MISS A BUNCH OF OTHER ESCAPE CHARS I'M (SO)*15 SORRY
            if esc_cmd == "[":                                  # UGUUUUUUUUuuuuuu~~~~~~~~
                esc_pattern = getch()
                if esc_pattern == "A": # UP ARROW 
                    if len(_buffer_history) > 0: 
                        if len(original_hist_string) == 0:
                            _push(_popped_history,string,permit_empty=True) # dont modify hist while scrolling,
                                                                            # you're allowed to push nothing just this once
                        else:
                            _push(_popped_history,original_hist_string)
                        original_hist_string = _buffer_history.pop() 
                        _swapWord(string,original_hist_string,cursor_index) 
                        cursor_index = len(original_hist_string)
                        string = original_hist_string

                elif esc_pattern == "B": # DOWN ARROW
                    if len(_popped_history) > 0:
                        _push(_buffer_history,string)
                        original_hist_string = _popped_history.pop()
                        _swapWord(string,original_hist_string,cursor_index)
                        cursor_index = len(original_hist_string)

                        string = original_hist_string
                    elif len(_popped_history) == 0: #save what you started to type at the bottom of pophist
                        original_hist_string = ""

                # TODO i havent figured out how to redraw all the shifted chars to the screen yet
                elif esc_pattern == "C": # right arrow
                    char = getch()
                    pass
                #     if cursor_index < len(string): 
                #         stdout.write(_CURSOR_MOVE_F)
                #         cursor_index += 1

                elif esc_pattern == "D": #left arrow
                    char = getch()
                    pass
                #     if cursor_index > 0:
                #         stdout.write(_CURSOR_MOVE_B)
                #         cursor_index -= 1

            else:
                # handle esc key + current key
                print "Weird char input. Mike, fix this shit." 
                # if no other esc conditions, reloop without getting new char (re-eval char after the esc from the top)
                char = esc_cmd
                continue
        else:
            string = _insertWithWrite(string,char,visible=visible,index=cursor_index)
            cursor_index += 1

            if len(string) >= _MAX_BUFF_SIZE and _MAX_BUFF_SIZE != _NO_BUFF_LIMIT:
                raise FilterInputException("Max string input size ("+str(_MAX_BUFF_SIZE)+") exceeded.")
        char = getch()

    if _should_buffer_history == True:
        if len(original_hist_string) != 0:
            _push(_buffer_history,original_hist_string)
        while len(_popped_history) > 0: # if theres stuff left in the new_stack, you selected from the old stack. 
                                        # replace all the hist items but the last one, that was what you were typing
                                        # before you scrolled up. this always works (?) because if you've typed nothing, it still counts as ""
            _push(_buffer_history,_popped_history.pop())
        _push(_buffer_history, string.rstrip())
    print ""
    return string.strip()

def _push(stack, item, permit_empty = False):
    if len(stack) > 0:
        if stack[len(stack)-1] == item: # I already got one, no thanks
            return
    if permit_empty:
        stack.append(item)
    else:
        if len(item) != 0:
            stack.append(item)

def _swapWord(word,replacement,cursor_index):
    for char in word:
        stdout.write(_BACKSPACE_HACK)
    stdout.write(replacement)

def _insertWithWrite(orig_word,to_insert,visible=True,index=-1):
    """
        insert or append a character to the string, reflect those changes in the terminal
        index == -1 means you're intending to append this to the end
        visible means you want this echoed
        Programmatically calling this with echoing fucks things, because you're inserting at index x, while the cursor isnt moving
    """
    # print "TRYING TO INSERT "+to_insert+" into "+orig_word+" at index "+str(index)
    if len(orig_word) == 0 or index == -1 or index == len(orig_word):
        if visible:
            stdout.write(to_insert)
        return orig_word+to_insert

    else: # redraw only the letters you insert and shift
        if visible:
            to_shift = orig_word[index:]
            stdout.write(to_insert+to_shift)
            for x in xrange(len(to_insert)+len(to_shift)):
                stdout.write(_CURSOR_MOVE_B)
        return orig_word[:index] + to_insert+ orig_word[index:]

def getStr(message=None):
    """
        gets a default string, you probably want to use this in place of raw_input
    """
    return getFilteredStr(message=message)

def getPass(message=None):
    """
        same as getStr() (raw_input replacement) but does not echo
    """
    return getFilteredStr(message = message, visible=False)

def getCh(message=None):
    """
        get a char from stdin without echoing
    """
    if message != None:
        print message,
    getch = _Getch()
    char = getch()
    return char

def bufferHistory(maxSize=5000, verbose=False):

    """
        set to NO_BUFF_LIMIT (-1) if you want to. admittedly, pylists will just go until memory overflow, but hey, it's your funeral cheif
    """
    if verbose:
        print "Buffering History, max size = "+str(maxSize)
    global _buffer_history
    global _popped_history
    global _should_buffer_history
    global _MAX_HIST_SIZE
    _MAX_HIST_SIZE = maxSize
    if _MAX_HIST_SIZE == NO_BUFF_LIMIT:
        _buffer_history = collections.deque()
        _popped_history = collections.deque()
    else:
        _buffer_history = collections.deque(maxlen=_MAX_HIST_SIZE)
        _popped_history = collections.deque(maxlen=_MAX_HIST_SIZE)
    _should_buffer_history = True

if __name__ == "__main__":
    bufferHistory()
    for x in xrange(25):
        word = getStr("Enter a word or something:")
        print "<|"+word+"|>"



