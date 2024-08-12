
import os, math
import numpy as np
from pymmio import files as mmio
from pymmio import ascii
from pyGrid.indx import INDX
from pyproj import Proj
from tqdm import tqdm


class SWS:
    km2 = 1.
    elv = 0.0
    ylat = 48.0
    xlng = -81.0
    slp = 0.0
    asp = 0.0

class Watershed:
    xr = dict() # swsid: [cell ids]
    t = dict() # ordered id: (from swsid, to swsid)
    s = dict() # swsid: SWS

    def __init__(self, fp=None, hdem=None, selection=None, epsg=3161):
        if hdem is None: return
        print(' loading ' + fp)
        idx = INDX(fp,hdem.gd)
        self.gd = hdem.gd
        topofp = mmio.removeExt(fp)+'.topo'
        if not os.path.exists(topofp): self.__writeTopo(topofp,idx,hdem)

        if selection != None:
            if type(selection) is list:
                self.xr = { k: idx.a[k] for k in selection } 
            elif type(selection) is set:
                self.xr = { k: idx.a[k] for k in selection }                 
            elif type(selection) is int:
                if hdem is None:
                    print('error: sws selection type int requires an hdem')
                    quit()                      
                lsel = set()
                for c in hdem.Climb(selection): lsel.add(idx.x[c])
                self.xr = { k: idx.a[k] for k in lsel }
                selection = list(lsel)
            else:
                print('error: sws selection type unknown')
                quit()                
        else: 
            self.xr = idx.a

        if os.path.exists(topofp):
            for ln in ascii.readCSV(topofp):
                sid = int(ln[1])
                dsid = int(ln[2])
                # dcid = int(ln[2])
                if selection != None: 
                    if not dsid in selection: continue
                    # if not dcid in selection: continue
                self.t[sid] = dsid #(disd, dcid) # {from swsid: (to swsid, to cid)}
        else:
            print('error: sws .topo not found')
            quit()

        # # check
        # for u,d in self.t.items():
        #     if d==-1:continue
        #     if d not in self.t:
        #         print("topo ERROR {}; {}".format(u,d))

        self.__buildSWS(hdem, selection, epsg)

    def __buildSWS(self, hdem, sel, epsg):        
        self.s = dict()
        ca = hdem.gd.cs**2
        pbar = tqdm(total=len(self.xr))
        # myProj = Proj('EPSG:26917') #("+proj=utm +zone=17N, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs")        
        myProj = Proj('EPSG:{}'.format(epsg))
        for k,v in self.xr.items():  
            pbar.update()          
            if sel != None: 
                if not k in sel: continue
            sx = 0.0
            sy = 0.0
            sz = 0.0
            sg = 0.0
            sgn = 0
            sax = 0.0
            say = 0.0
            sca = 0.0
            for cid in v:
                sca += ca
                tec = hdem.tem[cid]
                if tec.x==-9999:
                    i,j = hdem.gd.crc[cid]
                    cc = hdem.gd.cco[i][j]
                    sx += cc[0]
                    sy += cc[1]
                else:
                    sx += tec.x
                    sy += tec.y
                sz += tec.z
                if tec.g > 0: 
                    sg += tec.g
                    sgn += 1
                sax += math.sin(tec.a)
                say += math.cos(tec.a)

            n = len(v)
            ss = SWS()

            ss.km2 = sca / 1000 / 1000
            lg,ll = myProj(sx/n, sy/n, inverse=True)
            ss.ylat = ll
            ss.xlng = lg
            ss.elv = sz/n
            if sgn == 0 :
                ss.slp = 0.001
            else:
                ss.slp = sg/sgn
            ss.asp = (math.atan2(sax/n,say/n) + 2 * np.pi) % (2 * np.pi) # [0 to 2Pi] (raven requires [0 to 2Pi] over [-Pi to Pi])
            ss.rchlen = math.sqrt(n*ca*1e-6)
            self.s[k] = ss
        pbar.close()


    def __writeTopo(self, fp, sws, hdem):
        swsids = list(sws.a.keys())
        swsids.sort()
        with open(fp, "w") as f:
            f.write("linkID,upstream_swsID,downstream_swsID\n")
            k=0
            for u in swsids:
                k+=1
                if u < 0: continue
                # print("{} {}".format(u, sws.x[u]))
                x = list(hdem.fp[u].keys())
                if len(x)!=1: print("WARNING more than 1 downslope " + str(u))
                if x[0]<0: 
                    d=x[0]
                elif x[0] in sws.x:
                    d=sws.x[x[0]]
                else:
                    d=-1
                # self.t[k] = (u, d) # {ordered id: (from swsid, to swsid)}
                f.write("{},{},{}\n".format(k, u, d))


    def outlets(self):
        tt, o = set(), set()
        for _,t in self.t.items(): tt.add(t[0])
        for t in self.xr:
            if t in tt: continue
            o.add(int(t))
        return list(o)

    def saveToIndx(self,fp):
        a = dict()
        for sid,cids in self.xr.items():
            for cid in cids:
                a[cid] = sid
        self.gd.saveBinaryInt(fp,a)