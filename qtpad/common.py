#!/usr/bin/python3
import logging
import os

def getLogger():
    LOG_LEVEL = logging.INFO
    LOG_FORMAT_DATE = "%H:%M:%S"
    LOG_FORMAT = "%(levelname)s\t[%(asctime)s] %(message)s"
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_FORMAT_DATE)
    return logging.getLogger()

def getStaticPaths():
    LOCAL_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
    ICONS_DIR = LOCAL_DIR + 'icons/'
    PREFERENCES_FILE = os.path.expanduser("~/.config/qtpad/preferences.json")
    PROFILES_FILE = os.path.expanduser("~/.config/qtpad/profiles.json")
    return(LOCAL_DIR, ICONS_DIR, PREFERENCES_FILE, PROFILES_FILE)

def getNameIndex(prefix, db):
    try:
        split = prefix.rsplit(" ", 1)
        n = int(split[1])
        prefix = split[0]
    except (ValueError, IndexError):
        n = 1
    name = prefix + " " + str(n)
    while name in db:
        n += 1
        name = prefix + " " + str(n)
    return name

def copyDict(dictionnary):
    # from https://writeonly.wordpress.com/2009/05/07/deepcopy-is-a-pig-for-simple-data
    out = dict().fromkeys(dictionnary)
    for key, value in dictionnary.items():
        try:
            out[key] = value.copy()  # dicts, sets
        except AttributeError:
            try:
                out[key] = value[:]  # lists, tuples, strings, unicode
            except TypeError:
                out[key] = value  # ints
    return out
