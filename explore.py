#!/usr/bin/python3.9

from curses import wrapper
import os, subprocess, shutil, curses, time, pickle

class File:
    def __init__(self, filename, ext, timestamp):
        self.filename = filename
        self.ext = ext
        self.timestamp = timestamp
        self.star = ""
        self.rating = 0

def syncFilesDB(files, filesdb, fromDB):
    #return # FIXME
    toremove = []
    dbfiles = []
    if os.path.isfile(filesdb):
        dbfiles = pickle.load( open( filesdb, "rb" ) )
    else:
        dbfiles = []
        pickle.dump( dbfiles, open( filesdb, "wb" ) )

    for i, db_file in enumerate(dbfiles):
        updated_file = next((x for x in files if db_file.filename == x.filename), False)
        if not updated_file:
            toremove.append(i)
        elif fromDB:
            updated_file.star = db_file.star
            updated_file.rating = db_file.rating
        else:
            dbfiles[i].timestamp = updated_file.timestamp
            dbfiles[i].star = updated_file.star
            dbfiles[i].rating = updated_file.rating
            
    for i in toremove:
        del dbfiles[i]

    for i, file in enumerate(files):
        isfound = next((dbfile for dbfile in dbfiles if dbfile.filename == file.filename), False)
        if not isfound:
            dbfiles.append(file)

    pickle.dump( dbfiles, open( filesdb, "wb" ) )

def get_files(path, desired_ext):
    files = []
    allfiles = os.listdir(path)
    for i in range(0, len(allfiles)):
        f = allfiles[i]
        (file,ext) = os.path.splitext(f)
        if ext == desired_ext:
            stamp = os.path.getmtime(f)
            files.append(File(file, ext, stamp))
    return files

def draw_files(pad, files, selection, start_y, max_file_length, max_star_length, max_stamp_length):
    lineIndex = 0
    for i,f in enumerate(files):
        attr = curses.A_STANDOUT if i == selection else 0
        pad.addstr(start_y+i, 0, f.filename, attr)
        stampstr = time.asctime(time.localtime(f.timestamp))
        pad.addstr(start_y+i, max_file_length+1, stampstr, attr)
        pad.addstr(start_y+i, max_file_length+1+max_stamp_length+1, f.star, attr)
        pad.addstr(start_y+i, max_file_length+1+max_stamp_length+1+max_star_length+1, "*" * f.rating + " " * (5 - f.rating), attr)

def main(stdscr):
    curses.curs_set(0) # hide cursor
    screen = curses.initscr()
    pad = curses.newpad(100,100)

    filesdb = "filesdb.p"
    files = get_files(".", ".mp4")
    syncFilesDB(files, filesdb, True)
    selection=0
    max_file_length = max(len(f.filename) for f in files)
    max_stamp_length = len(time.asctime())
    max_star_length = max(len("star"), max(len(f.star) for f in files))

    pad.addstr(0, 0, "filename", curses.A_BOLD)
    pad.addstr(0, max_file_length+1, "last modif", curses.A_BOLD)
    pad.addstr(0, max_file_length+1+max_stamp_length+1, "star", curses.A_BOLD)
    pad.addstr(0, max_file_length+1+max_stamp_length+1+max_star_length+1, "rating", curses.A_BOLD)
    pad.addstr(1, 0, "=" * 100, curses.A_BOLD)

    header= 2
    max_y = 22
    files_max_y = max_y - header
    
    while(True):
        draw_files(pad, files, selection, header, max_file_length, max_star_length, max_stamp_length)
        pad_y = selection - files_max_y if selection > files_max_y else 0
        pad.refresh(pad_y, 0, 0, 0, max_y, 79)

        key = screen.getkey()
        if key == "KEY_DOWN":
            selection = min(selection+1, len(files)-1)
        elif key == "KEY_UP":
            selection = max(selection-1, 0)
        elif key == "KEY_LEFT":
            files[selection].rating = max(0, files[selection].rating-1)
            syncFilesDB(files, filesdb, False)
        elif key == "KEY_RIGHT":
            files[selection].rating = min(5, files[selection].rating+1)
            syncFilesDB(files, filesdb, False)
        elif key == "e":
            files[selection].star = pad.getstr()
            syncFilesDB(files, filesdb, False)
            max_star_length = max(len("star"), max(len(f.star) for f in files))
        elif key == "\n":
            selectedFile = files[selection].filename + files[selection].ext
            subprocess.run(["mplayer", f'{os.path.abspath(selectedFile)}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif key == "q" or key == "Q":
            exit()

wrapper(main)
