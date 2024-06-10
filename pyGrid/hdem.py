
import os, struct
import numpy as np
from pymmio import files as mmio
from pyGrid.definition import GDEF
# import sys
# sys.setrecursionlimit(10**5)


class tec:
    def __init__(self, x, y, z, gradient, aspect):
        self.x = x
        self.y = y
        self.z = z
        self.g = gradient
        self.a = aspect

class HDEM:
    gd = GDEF
    tem = None
    fp = None
    us = None

    def __init__(self, filepath, skipflowpaths=False):      

        gdfp = filepath+".gdef" # mmio.removeExt(filepath)+".gdef"
        if not os.path.exists(gdfp):
            gdfp = mmio.removeExt(filepath)+".gdef"
            if not os.path.exists(gdfp):
                print('error no grid definition file available: ',gdfp,'\n')
                quit()
        self.gd = GDEF(gdfp)

        print(' loading', filepath)

        ext = mmio.getExtension(filepath)
        if ext == '.uhdem':
            self.__loadUHDEM(filepath,skipflowpaths)
        elif ext == '.hdem':
            self.__loadHDEM(filepath,skipflowpaths)
        else:
            print("error: unsupported HDEM format\n")
            quit()

    def __loadHDEM(self,filepath,skipflowpaths):
        a = np.fromfile(filepath, float, 3*self.gd.nrow*self.gd.ncol).reshape(self.gd.nrow, self.gd.ncol, 3)
        cxy = self.gd.cco
        self.tem = dict()
        for c,rc in self.gd.crc.items():
            x,y = cxy[rc]
            z,g,s = a[rc]
            self.tem[c] = tec(x,y,z,g,s)

        if not skipflowpaths: print(' ** TODO: HDEM flowpaths not read **')


    def __loadUHDEM(self,filepath,skipflowpaths):
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

                if skipflowpaths: return
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

    def CatchmentArea(self,cid):
        lst = self.Climb(cid)
        return self.gd.cs*self.gd.cs*len(lst)
 
    def Crop(self, gd):
        if self.gd.ncell == gd.ncell: return # naive assumption, might fail
        print('  cropping TEM..')
        newact = set(gd.ActiveIDs())
        newtem = dict()
        for k,v in self.tem.items():
            if k in newact: newtem[k] = v

        if self.fp is not None:
            newfp = dict()
            for k,v in self.fp.items():
                if k in newact:
                    s = 0
                    newfp[k] = dict()
                    for kk,vv in v.items():
                        if kk in newact:
                            newfp[k][kk]=vv
                            s+=vv
                    if s != 1:
                        for kk,vv in newfp[k].items():
                            newfp[k][kk] /= s

        if self.us is not None:
            print('ERROR TODO: tem.Crop need to crop upslopes............')

        self.gd = gd