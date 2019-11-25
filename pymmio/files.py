
import os

def mkDir(path):
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

def dirList(directory, ext=""):
    lst = list()
    for filename in os.listdir(directory):
        if len(ext) > 0:            
            if filename.endswith(ext): 
                lst.append(os.path.join(directory, filename))
        else: 
            lst.append(os.path.join(directory, filename))
    return(lst)

def removeExt(fp):
    return(os.path.splitext(fp)[0])

def getExtension(fp): # returns as '.ext'
    return(os.path.splitext(fp)[1])

def getFileName(fp,rmExt=True):
    base=os.path.basename(fp)
    if rmExt: return(removeExt(base))
    return(base)

def readFloats(fp):
    with open(fp) as f:
        return [float(x) for x in f]

def readIntFloats(fp):
    with open(fp) as f:
        lines = (line.split('\t') for line in f)
        return dict((int(k), float(v)) for k, v in lines)        