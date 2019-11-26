
import os
import struct
from pymmio import files
from pyGrid.definition import gdef
import sys
sys.setrecursionlimit(2000)


class tec:
    def __init__(self, x, y, z, gradient, aspect):
        self.x = x
        self.y = y
        self.z = z
        self.g = gradient
        self.a = aspect

class hdem:
    gd = gdef
    tem = None
    fp = None
    us = None

    def __init__(self, filepath):        
        gdfp = filepath+".gdef" # files.removeExt(filepath)+".gdef"
        if not os.path.exists(gdfp):
            print('error no grid definition file available: ',gdfp,'\n')
            quit()
        if files.getExtension(filepath)!=".uhdem": 
            print("error: only .uhdem's supported ',filepath,'\n")
            quit()

        self.gd = gdef(gdfp)
        print(' loading', filepath)
        self.loadUHDEM(filepath)       

    def loadUHDEM(self,filepath):
        # THIS IS VERY SLOW!!!!
        try:
            with open(filepath, 'rb') as f:
                # read DEM data
                nl = struct.unpack('<b', f.read(1))[0]
                hd = struct.unpack('<{}c'.format(nl), f.read(nl)) # 'unstructured'
                if str(b''.join(hd)) != "b'unstructured'":
                    print("uhden error: invalid header format'\n")
                    quit()

                print('  reading TEM..')
                nc = struct.unpack('<i', f.read(4))[0]
                tta = struct.unpack('<' + 'iddddd'*nc, f.read(44*nc))
                ttt = [i for i in zip(*[iter(tta)]*6)] # convering long list to list of tuples. see: https://stackoverflow.com/questions/23286254/convert-list-to-a-list-of-tuples-python
                self.tem = {k:tec(x,y,z,g,a) for k,x,y,z,g,a in ttt}

                try:
                    nfp = struct.unpack('<i', f.read(4))[0]  
                    print('  reading flowpaths..')                
                    self.fp = dict()
                    for _ in range(nfp):
                        cid = struct.unpack('<i', f.read(4))[0]
                        if cid == '': break # EOF                        
                        ndn = struct.unpack('<i', f.read(4))[0]
                        self.fp[cid] = dict()
                        for _ in range(ndn):
                            idn = struct.unpack('<i', f.read(4))[0]
                            fdn = struct.unpack('<d', f.read(8))[0]
                            self.fp[cid][idn]=fdn
                except EOFError:
                    pass # no flowpaths
                except Exception as err:
                    print('error reading hdem file:',filepath,'\n',err)
                    quit()
        except FileNotFoundError:
            print(' hdem file:',filepath,'not found.')
            quit()
        except Exception as err:
            print('error reading hdem file:',filepath,'\n',err)
            quit()

    def BuildUpslopes(self):
        print('  building upslopes..')
        self.us = dict()
        for fid,tids in self.fp.items():
            for tid in tids.keys():
                if tid in self.us:
                    self.us[tid].append(fid)
                else:
                    self.us[tid]=[fid]

    def Climb(self,cid):
        # NOTE: recursion not well suited to python !!!!!!!!!!!!!!
        if self.us==None: self.BuildUpslopes()
        sColl = set()
        def pclimb(cid):
            sColl.add(cid)
            if cid in self.us:
                for u in self.us[cid]:
                    if u in sColl: continue                
                    pclimb(u)
        pclimb(cid)
        return(list(sColl))

