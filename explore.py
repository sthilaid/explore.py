#!/usr/bin/python3.9

from curses import wrapper
import os, subprocess, shutil, curses, time, pickle, sys, curses.textpad

sortfns = [lambda x: x.filename,
               lambda x: x.timestamp,
               lambda x: x.filesize,
               lambda x: x.rating,
               lambda x: x.star,
               ]
sortkey = 0
sortdir = 0
max_file_length = 0
max_stamp_length = 0
max_fsize_length = 0
max_star_length = 0
max_rating_length = 0
lastsizex = 0
lastsizey = 0
windowx = 0
windowy = 0

class File:
    def __init__(self, filename, ext, timestamp, fsize):
        self.filename = filename
        self.ext = ext
        self.timestamp = timestamp
        self.filesize = fsize
        self.isMarkedForDeletion = False
        self.star = ""
        self.rating = 0

def update_size(screen):
    global windowy, windowx
    y, x = screen.getmaxyx()
    if y != windowy or x != windowx:
        windowy, windowx = y, x
        #screen.clear()
        curses.resizeterm(windowy, windowx)
        #screen.refresh()

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
            dbfiles[i].star = updated_file.star
            dbfiles[i].rating = updated_file.rating
            
    for i in reversed(sorted(toremove)):
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
            stamp = os.path.getmtime(path+"/"+f)
            fsize = os.path.getsize(path+"/"+f)
            files.append(File(file, ext, stamp, fsize))
    return files

def draw_title(pad):
    global max_file_length, max_stamp_length, max_fsize_length, max_rating_length, max_star_length, sortkey, sortdir

    msg = "filename" + ("▲" if (sortkey == 0 and sortdir == 0) else ("▼" if (sortkey == 0 and sortdir == 1) else " "))
    pad.addstr(0, 0, msg, curses.A_BOLD)

    offset=max_file_length+1
    msg = "last modif" + ("▲" if (sortkey == 1 and sortdir == 0) else ("▼" if (sortkey == 1 and sortdir == 1) else " "))
    pad.addstr(0, offset, msg, curses.A_BOLD)
    
    offset += max_stamp_length+1
    msg = "size" + ("▲" if (sortkey == 2 and sortdir == 0) else ("▼" if (sortkey == 2 and sortdir == 1) else " "))
    pad.addstr(0, offset, msg, curses.A_BOLD)
    
    offset += max_fsize_length+1
    msg = "rating" + ("▲" if (sortkey == 3 and sortdir == 0) else ("▼" if (sortkey == 3 and sortdir == 1) else " "))
    pad.addstr(0, offset, msg, curses.A_BOLD)
    
    offset += max_rating_length+1
    msg = "star" + ("▲" if (sortkey == 4 and sortdir == 0) else ("▼" if (sortkey == 4 and sortdir == 1) else " "))
    pad.addstr(0, offset, msg, curses.A_BOLD)
    pad.addstr(0, offset+5, " " * 60, curses.A_BOLD)
    pad.addstr(1, 0, "=" * 100, curses.A_BOLD)

def draw_files(pad, files, selection):
    global max_file_length, max_star_length, max_rating_length, max_stamp_length, max_fsize_length
    lineIndex = 0
    for i,f in enumerate(files):
        attr = curses.A_STANDOUT if i == selection else 0
        pad.addstr(i, 0, "D " if f.isMarkedForDeletion else "  ", attr)
        pad.addstr(i, 2, f.filename, attr)
        pad.addstr(i, 2+len(f.filename), " "*(max_file_length - len(f.filename)), attr)

        stampstr = time.asctime(time.localtime(f.timestamp))+" "
        xoffset = max_file_length+1
        pad.addstr(i, xoffset, stampstr, attr)

        xoffset += max_stamp_length+1
        pad.addstr(i, xoffset, '{:.2f} GB '.format(f.filesize*0.000000001), attr);

        xoffset += max_fsize_length+1
        pad.addstr(i, xoffset, "*" * f.rating + " " * (5 - f.rating)+"  ", attr)

        xoffset += max_rating_length+1
        pad.addstr(i, xoffset, f.star, attr)
        pad.addstr(i, xoffset+len(f.star), " "*40, attr)

def main(stdscr):
    global sortkey, sortdir, max_file_length, max_stamp_length, max_fsize_length, max_star_length, max_rating_length
    global lastsizey, lastsizex
    
    curses.curs_set(0) # hide cursor
    screen = curses.initscr()
    titlepad = curses.newpad(3,100)
    pad = curses.newpad(100,100)
    update_size(screen)

    # boxwindow = curses.newwin(5,30,2,1)
    # box = curses.textpad.Textbox(boxwindow)

    rootFolder = "."
    extensionFilter = ""
    cmdProcess = "echo"
    filesdb = ".filesdb"
    
    if len(sys.argv) > 1:
        rootFolder = sys.argv[1]
        if len(sys.argv) > 2:
            extensionFilter = sys.argv[2]
            if len(sys.argv) > 3:
                cmdProcess = sys.argv[3]
                if len(sys.argv) > 4:
                    filesdb = sys.argv[4]

    files = get_files(rootFolder, extensionFilter)
    syncFilesDB(files, rootFolder+"/"+filesdb, True)
    files.sort(key=sortfns[sortkey], reverse=(sortdir==1))

    if len(files) == 0:
        return
    
    selection=0
    max_file_length = 2 + max(len(f.filename) for f in files) # 2 for Deletion flag
    max_stamp_length = len(time.asctime())
    max_fsize_length = 7
    max_star_length = max(len("star"), max(len(f.star) for f in files))
    max_rating_length = 6

    titlepad.refresh(0, 0, 0, 0, 2, windowx-1)
    draw_title(titlepad)

    header= 3
    while(True):
        update_size(screen)
        files_max_y = max(0,windowy - header)
        draw_files(pad, files, selection)

        titlepad.refresh(0, 0, 0, 0, 2, windowx-1)
        
        pad_y = selection - files_max_y if selection > files_max_y else 0
        pad.refresh(pad_y, 0, 2, 0, windowy-1, windowx-1)

        key = screen.getkey()
        if key == "KEY_DOWN":
            selection = min(selection+1, len(files)-1)
        elif key == "KEY_UP":
            selection = max(selection-1, 0)
        elif key == "KEY_LEFT":
            files[selection].rating = max(0, files[selection].rating-1)
            syncFilesDB(files, rootFolder+"/"+filesdb, False)
        elif key == "KEY_RIGHT":
            files[selection].rating = min(5, files[selection].rating+1)
            syncFilesDB(files, rootFolder+"/"+filesdb, False)
        elif key == "e":
            input = pad.getstr().decode("utf-8")
            # box.edit()
            # input = box.gather()
            files[selection].star = input if input else ""
            syncFilesDB(files, rootFolder+"/"+filesdb, False)
            max_star_length = max(len("star"), max(len(f.star) for f in files))
            draw_title(titlepad)
        elif key == "\n":
            selectedFile = rootFolder+"/"+files[selection].filename + files[selection].ext
            subprocess.run([cmdProcess, f'{os.path.abspath(selectedFile)}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif key == "d":
            files[selection].isMarkedForDeletion = not files[selection].isMarkedForDeletion
        elif key == "x":
            for f in files:
                if f.isMarkedForDeletion:
                    filename = rootFolder+"/"+f.filename + f.ext
                    if os.path.isfile(filename):
                        os.remove(filename)
                    else:
                        shutil.rmtree(filename)
            files = [f for f in files if not f.isMarkedForDeletion]
            syncFilesDB(files, rootFolder+"/"+filesdb, False)
            pad.clear()
            draw_title(titlepad)
            draw_files(pad, files, selection)
        elif key == "s":
            if sortdir == 0:
                sortdir = 1
            else:
                sortdir = 0
                sortkey = (sortkey +1) % len(sortfns)
            files.sort(key=sortfns[sortkey], reverse=(sortdir==1))
            draw_title(titlepad)
        elif key == "q" or key == "Q":
            exit()
            
wrapper(main)
