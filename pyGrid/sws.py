
import os, math
import numpy as np
import shapefile
from pymmio import files as mmio
# from pymmio import ascii
# from pyGrid.indx import INDX
# from pyGrid.real import REAL
# from pyGrid.hdem import HDEM
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
    haschans = False # True if channel parameters are specified
    info = dict()

    def __init__(self, fp=None, hdem=None, selection=None, epsg=3161):
        if fp is None and hdem is None: 
            self.xr = dict() 
            self.t = dict()  
            self.d = dict()  
            self.s = dict()  
            self.nam = dict()
            self.lak = dict()
            self.gag = dict()
            self.info = dict()
            return
        
        ord = dict() # swsid: outlet (strahler) stream order
        chanwidth = dict() # swsid: outlet channel width
        valleywidth = dict() # swsid: outlet outlet floodplain width (if <= chanwidth, assumes trapezoidal channel)
        chanrough = dict() # swsid: outlet channel roughness
        floodplrough = dict() # swsid: outlet floodplain roughness
        if mmio.getExtension(fp)=='.shp':
            sf = shapefile.Reader(fp)
            geom = sf.shapes()
            # feld = sf.fields # see field names
            attr = sf.records()
            for i in range(len(geom)):
                a = attr[i]
                # print(a)
                sid = int(a.SubId)
                self.xr[sid] = hdem.gd.polygonToCellIDs(geom[i].points)
                self.t[sid] = int(a.DowSubId)
                self.nam[sid] = a.rvhName
                self.gag[sid] = a.gauge
                if hasattr(a, 'lake'): self.lak[sid] = a.lake != 0
                if hasattr(a, 'strahler'): ord[sid] = a.strahler
                if hasattr(a, 'wchan'): chanwidth[sid] = a.wchan
                if hasattr(a, 'wflood'): valleywidth[sid] = a.wflood
                if hasattr(a, 'nchan'): chanrough[sid] = a.nchan
                if hasattr(a, 'nflood'): floodplrough[sid] = a.nflood
                # print(len(self.xr[sid])*hdem.gd.cs*hdem.gd.cs/1000000)
            if not os.path.exists(fp+'-swsid.bil'):
                out = np.full(hdem.gd.ncol*hdem.gd.nrow,-9999)
                for sid, cids in self.xr.items():
                    for c in cids: out[c]=sid
                hdem.gd.saveBinaryInt(fp+'-swsid.bil',out)
        else:
            print('error: sws.py todo (look below)')
            quit()

        # if type(hdem) is REAL:
        #     sf = shapefile.Reader(fp)
        #     geom = sf.shapes()
        #     # feld = sf.fields # see field names
        #     attr = sf.records()
        #     for i in range(len(geom)):
        #         # print(attr[i])
        #         sid = int(attr[i].SubId)
        #         self.xr[sid] = hdem.gd.polygonToCellIDs(geom[i].points)
        #         self.t[sid] = int(attr[i].DowSubId)
        #         self.nam[sid] = attr[i].rvhName
        #         self.gag[sid] = attr[i].gauge
        #         self.lak[sid] = attr[i].lake != 0
        #         # print(len(self.xr[sid])*hdem.gd.cs*hdem.gd.cs/1000000)
        #     if not os.path.exists(fp+'-swsid.bil'):
        #         out = np.full(hdem.gd.ncol*hdem.gd.nrow,-9999)
        #         for sid, cids in self.xr.items():
        #             for c in cids: out[c]=sid
        #         hdem.gd.saveBinaryInt(fp+'-swsid.bil',out)
        # elif type(hdem) is HDEM:
        #     print(' loading ' + fp)
        #     idx = INDX(fp,hdem.gd)
        #     self.gd = hdem.gd
        #     topofp = mmio.removeExt(fp)+'.topo'
        #     if not os.path.exists(topofp): self.__writeTopo(topofp,idx,hdem)

        #     if selection != None:
        #         if type(selection) is list:
        #             self.xr = { k: idx.a[k] for k in selection } 
        #         elif type(selection) is set:
        #             self.xr = { k: idx.a[k] for k in selection }                 
        #         elif type(selection) is int:
        #             if hdem is None:
        #                 print('error: sws selection type int requires an hdem')
        #                 quit()                      
        #             lsel = set()
        #             for c in hdem.Climb(selection): lsel.add(idx.x[c])
        #             self.xr = { k: idx.a[k] for k in lsel }
        #             selection = list(lsel)
        #         else:
        #             print('error: sws selection type unknown')
        #             quit()                
        #     else: 
        #         self.xr = idx.a

        #     if os.path.exists(topofp):
        #         for ln in ascii.readCSV(topofp):
        #             sid = int(ln[1])
        #             dsid = int(ln[2])
        #             # dcid = int(ln[2])
        #             if selection != None: 
        #                 if not dsid in selection: continue
        #                 # if not dcid in selection: continue
        #             self.t[sid] = dsid #(disd, dcid) # {from swsid: (to swsid, to cid)}
        #     else:
        #         print('error: sws .topo not found')
        #         quit()

        #     # # check
        #     # for u,d in self.t.items():
        #     #     if d==-1:continue
        #     #     if d not in self.t:
        #     #         print("topo ERROR {}; {}".format(u,d))
        # else:
        #     print('watershed.__init__ error: unknown dem type:',type(hdem))
        #     quit()

        self.__buildSWS(hdem, selection, epsg)
        for t in self.xr:
            if t in chanwidth: 
                self.s[t].chanwidth = chanwidth[t]
                self.s[t].valleywidth = 0.0
                self.s[t].chanrough = 0.0
                self.s[t].floodplrough = 0.0
                self.s[t].ord = -1
                self.haschans = True            
            if t in ord: self.s[t].ord = ord[t]
            if t in valleywidth: self.s[t].valleywidth = valleywidth[t]
            if t in chanrough: self.s[t].chanrough = chanrough[t]
            if t in floodplrough: self.s[t].floodplrough = floodplrough[t]


    def __buildSWS(self, hdem, sel, epsg):        
        self.s = dict()
        ca = hdem.gd.cs**2
        z, g, a = dict(), dict(), dict()
        for c, tec in hdem.tem.items():
            z[c] = tec.z
            g[c] = tec.g
            a[c] = tec.a

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

            for cid in v:
                sca += ca
                i,j = hdem.gd.crc[cid]
                cc = hdem.gd.cco[i][j]
                if z[cid] > -999:
                    sx += cc[0]
                    sy += cc[1]
                    sz += z[cid]
                    n += 1
                    if g[cid] > 0: 
                        sg += g[cid]
                        sgn += 1
                        sax += math.sin(a[cid])
                        say += math.cos(a[cid])

            ss = SWS()
            ss.km2 = sca / 1000 / 1000
            lg,ll = myProj(sx/n, sy/n, inverse=True)
            ss.ylat = ll
            ss.xlng = lg
            ss.elv = sz/n
            if sgn == 0 :
                ss.slp = 0.
                ss.asp = 0.
            else:
                ss.slp = math.atan(sg/sgn) # rad
                ss.asp = (math.atan2(sax/sgn,say/sgn) + 2 * np.pi) % (2 * np.pi) # [0 to 2Pi] (raven requires [0 to 2Pi] over [-Pi to Pi])
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
        if type(wid)==int:
            wids = self.climb(wid)
            for uw in wids:
                out.xr[uw] = self.xr[uw]
                out.t[uw] = self.t[uw]
                out.s[uw] = self.s[uw]
                out.nam[uw] = self.nam[uw]
                out.lak[uw] = self.lak[uw]
                out.gag[uw] = self.gag[uw]
                out.haschans = self.haschans
        elif type(wid)==list:
             for w in wid:
                out.xr[w] = self.xr[w]
                out.t[w] = self.t[w]
                out.s[w] = self.s[w]
                out.nam[w] = self.nam[w]
                out.lak[w] = self.lak[w]
                out.gag[w] = self.gag[w]
                out.haschans = self.haschans           
        return out

    def saveToIndx(self,fp):
        a = dict()
        for sid,cids in self.xr.items():
            for cid in cids:
                a[cid] = sid
        self.gd.saveBinaryInt(fp,a)