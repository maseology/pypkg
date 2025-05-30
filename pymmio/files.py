
import os, shutil
import unicodedata, re

def mkDir(path,prnt=True):
    if os.path.isdir(path): return
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        if prnt: print (" Successfully created the directory %s " % path)

def dirList(directory, ext="", recursive=True):
    lst = list()
    if recursive:
        for root, _, files in os.walk(directory):
            for filename in files:
                if len(ext) > 0:
                    if filename.lower().endswith(ext.lower()): 
                        lst.append(os.path.join(root, filename))
                else:
                    lst.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            if len(ext) > 0:
                if filename.lower().endswith(ext.lower()): 
                    lst.append(os.path.join(directory, filename))
            else: 
                lst.append(os.path.join(directory, filename))
    return(lst)

def deleteDir(directory):
    shutil.rmtree(directory)

def deletefile(fp):
    if os.path.exists(fp): os.remove(fp)

def removeExt(fp):
    return(os.path.splitext(fp)[0])

def getExtension(fp): # returns as '.ext'
    return(os.path.splitext(fp)[1])

def getFileName(fp,rmExt=True):
    base=os.path.basename(fp)
    if base == '': base = os.path.split(os.path.split(fp)[0])[1]
    if rmExt: return(removeExt(base))
    return(base)

def getFileDir(fp):
    return os.path.dirname(os.path.realpath(fp))

def fileNameClean(fp, allow_unicode=False):
    # from https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    fp = str(fp)
    if allow_unicode:
        fp = unicodedata.normalize('NFKC', fp)
    else:
        fp = unicodedata.normalize('NFKD', fp).encode('ascii', 'ignore').decode('ascii')
    fp = re.sub(r'[^\w\s-]', '', fp.lower())
    return re.sub(r'[-\s]+', '-', fp).strip('-_')    