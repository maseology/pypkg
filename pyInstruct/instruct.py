
import re, json
from pymmio import ascii, files

# pyInstruct is a set of general routines built to read instruction files for a variety model build procedures

class build():
    desc = ""
    root = ""
    params = dict()

    def __init__(self, filepath):
        self.__read(filepath)
        self.params =  {k.lower(): v for k, v in self.params.items()} # converting all to lower case        

    def __read(self, fp):
        print("\nReading: " + fp + " ...\n")
        self.root = files.getFileDir(fp) + '\\'
        ss = ""
        skip = False
        for ln in ascii.readLines(fp):

            # commented out            
            if ln[0]=='!': continue
            if ln.find('!') > -1: ln = ln[0:ln.find('!')].strip()
            
            ln = re.split(r'\t+', ln) # tab-delimited

            # block skipping            
            if ln[0][:8].lower()=='skip off': 
                skip=False
                continue

            if skip: continue

            if ln[0][:7].lower()=='skip on': 
                skip=True
                continue                   

            # parameter subsets
            if len(ss)>0:
                if ln[0][:3].lower()=="end":                     
                    ss = ""
                    continue
                v = self.__parsep(ln)
                self.params[ss][v[0]]=v[1]
                continue
                                    
            if ln[0][:5].lower()=="begin": 
                ss = ln[0][6:].strip()
                self.params[ss] = dict()
                continue

            # global settings/parameters
            if ln[0].lower()=="description": 
                self.desc = ln[1]
                continue

            v = self.__parsep(ln)
            self.params[v[0]]=v[1]       


    def __parsep(self,splitline):
        if len(splitline)==1:
            return splitline[0], True
        elif len(splitline)==2:
            if splitline[1].isnumeric():
                if splitline[1].find(".")==-1: 
                    return splitline[0], int(splitline[1])
                else:
                    return splitline[0], float(splitline[1])
            elif splitline[1].lower() in ['true']:
                return splitline[0], True
            elif splitline[1].lower() in ['false']:
                return splitline[0], False
            elif splitline[1][0]=='{' or splitline[1][0]=='[':
                if splitline[1].find(":")>-1:
                    return splitline[0], json.load(splitline[1])
                else:
                    l = splitline[1][1:len(splitline[1])-1].split(',')
                    l = [i.strip() for i in l]
                    try:
                        l = [int(i) for i in l]
                    except:
                        try:
                            l = [float(i) for i in l]
                        except:
                            pass
                    return splitline[0], l
            else:
                return splitline[0], splitline[1]
        else:
            return splitline[0], splitline[1:]

    def FilePath(self,parnam):
        return self.root + self.params[parnam]

    def print(self):        
        if len(self.desc) == 0: 
            print('='*17 + " MODFLOW6 builder")
        else:
            print(" " + '='*(13 + len(self.desc)))
            print(" Description: " + self.desc)
            print(" " + '='*(13 + len(self.desc)))
        print() #" Parameters:")
        for k,v in self.params.items():
            if type(v) is dict:
                print("   {}:".format(k))
                for k1,v1 in v.items():
                    print("     {}: {}".format(k1,v1))
            else:
                print("   {}:\t{}".format(k,v))
        print()