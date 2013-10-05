# clean_up_twl.py

from tempfile import mkstemp
from shutil import move
from os import remove, close

"""
    util to clean up the block of text at 
    http://kisa.ca/scrabble/
    so I can use it with enchant is a wordlist
"""
def replace(file_path, pattern, subst):
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(file_path)
    for line in old_file:
        new_file.write(line.replace(pattern, subst))
    new_file.close()
    close(fh)
    old_file.close()
    #Remove original file
    #remove(file_path) #do you really want to huuuurt meeee
    #Move new file
    move(abs_path, "cleaned_"+file_path)

if __name__ == "__main__":
    print "Cleaning..."
    replace("twl.txt"," ","\n")
    print "Done."