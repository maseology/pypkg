
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

    def __init__(self, fp, hdem, selection=None):
        print(' loading ' + fp)
        idx = INDX(fp,hdem.gd)
        self.xr = { k: idx.a[k] for k in selection }
        if os.path.exists(mmio.removeExt(fp)+'.topo'):
            for ln in ascii.readCSV(mmio.removeExt(fp)+'.topo'):
                k = int(ln[0])
                u = int(ln[1])
                d = int(ln[2])
                if selection != None: 
                    if not u in selection: continue
                    if not d in selection: continue
                self.t[k] = (u, d) # {ordered id: (from swsid, to swsid)}
        else:
            print('error: sws .topo not found')
            quit()

        self.__buildSWS(hdem, selection)

    def __buildSWS(self, hdem, sel):        
        self.s = dict()
        ca = hdem.gd.cs**2
        pbar = tqdm(total=len(self.xr))
        myProj = Proj("+proj=utm +zone=17N, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs")        
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