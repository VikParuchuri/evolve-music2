from config import settings
import os
import random
import re

mdir = settings.MUSIC_STORE_PATH

files = [f for f in os.listdir(mdir) if f.endswith(".ogg")]

wordlistfile = os.path.abspath(os.path.join(settings.PROJECT_PATH, "data", "wordlist.txt"))
words = open(wordlistfile).read().split("\r\n")

for f in files:
    try:
        date = re.search('\d+-\d+-\d+-\d+', f).group(0)
    except Exception:
        continue
    word_length = random.randint(1,2)
    new_name = []
    for i in xrange(0,word_length):
        new_name.append(random.choice(words))
    name = "_".join(new_name)
    full_filepath = os.path.abspath(os.path.join(mdir,f))
    new_filepath = os.path.abspath(os.path.join(mdir,name+date+".ogg"))
    os.rename(full_filepath,new_filepath)