
import os, math
import numpy as np
import shapefile
from pymmio import files as mmio
from pymmio import ascii
from pyGrid.indx import INDX
from pyGrid.real import REAL
from pyGrid.hdem import HDEM
from pyproj import Proj
from tqdm import tqdm


class SWS:
    km2 = 1.
    elv = 0.0
    ylat = 48.0
    xlng = -81.0
    slp = 0.0
    asp = 0.0
    rchlen = 0.0

class Watershed:
    xr = dict() # swsid: [cell ids]
    t = dict()  # swsid: downswsid  # ordered id: (from swsid, to swsid)
    d = dict()  # downswsid: [swsid]
    s = dict()  # swsid: SWS
    nam = dict() # swsid: name
    lak = dict() # is lake?
    gag = dict() # swsid: gauge name

    def __init__(self, fp=None, hdem=None, selection=None, epsg=3161):
        if fp is None and hdem is None: 
            self.xr = dict()
            self.t = dict()
            self.d = dict()
            self.s = dict()
            self.nam = dict()
            self.lak = dict()
            self.gag = dict()
            return
        if type(hdem) is REAL:
            sf = shapefile.Reader(fp)
            geom = sf.shapes()
            # feld = sf.fields # see field names
            attr = sf.records()
            for i in range(len(geom)):
                # print(attr[i])
                sid = int(attr[i].SubId)
                self.xr[sid] = hdem.gd.polygonToCellIDs(geom[i].points)
                self.t[sid] = int(attr[i].DowSubId)
                self.nam[sid] = attr[i].rvhName
                self.gag[sid] = attr[i].gauge
                self.lak[sid] = attr[i].lake != 0
                # print(len(self.xr[sid])*hdem.gd.cs*hdem.gd.cs/1000000)
            if not os.path.exists(fp+'-swsid.bil'):
                out = np.full(hdem.gd.ncol*hdem.gd.nrow,-9999)
                for sid, cids in self.xr.items():
                    for c in cids: out[c]=sid
                hdem.gd.saveBinaryInt(fp+'-swsid.bil',out)
        elif type(hdem) is HDEM:
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
        else:
            print('watershed.__init__ error: unknown dem type:',type(hdem))
            quit()

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
            n = 0
            sx = 0.0
            sy = 0.0
            sz = 0.0
            sg = 0.0
            sgn = 0
            sax = 0.0
            say = 0.0
            sca = 0.0
            if type(hdem)==REAL:
                for cid in v:
                    sca += ca
                    i,j = hdem.gd.crc[cid]
                    cc = hdem.gd.cco[i][j]
                    if hdem.x[cid] > -999:
                        sx += cc[0]
                        sy += cc[1]
                        sz += hdem.x[cid]
                        n += 1
            else:
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
        for _,t in self.t.items(): tt.add(t)
        for t in self.xr:
            if t in tt: continue
            o.add(int(t))
        return list(o)

    def climb(self, wid):
        if len(self.d)==0:
            for k,v in self.t.items():
                if v in self.d:
                    self.d[v].append(k)
                else:
                    self.d[v] = [k]
        wids = list()
        def recurse(wid):
            wids.append(wid)
            if wid in self.d:
                for uw in self.d[wid]:
                    recurse(uw)
        recurse(wid)
        return wids

    def subset(self, wid):
        out = Watershed()
        wids = self.climb(wid)
        for uw in wids:
            out.xr[uw] = self.xr[uw]
            out.t[uw] = self.t[uw]
            out.s[uw] = self.s[uw]
            out.nam[uw] = self.nam[uw]
            out.lak[uw] = self.lak[uw]
            out.gag[uw] = self.gag[uw]
        return out

    def saveToIndx(self,fp):
        a = dict()
        for sid,cids in self.xr.items():
            for cid in cids:
                a[cid] = sid
        self.gd.saveBinaryInt(fp,a)