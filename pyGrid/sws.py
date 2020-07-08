
import os, math
import numpy as np
from pymmio import files as mmio
from pymmio import ascii
from pyGrid.indx import indx
from pyproj import Proj
from tqdm import tqdm


class SWS:
    ca = 1.
    km2 = 1.
    elv = 0.0
    ylat = 48.0
    xlng = -81.0
    slp = 0.0
    asp = 0.0

class Watershed:
    pass

    def __init__(self, fp, hdem):
        print(' loading ' + fp)
        idx = indx(fp,hdem.gd)
        self.a = idx.a
        self.t = dict()
        if os.path.exists(mmio.removeExt(fp)+'.topo'):
            for ln in ascii.readCSV(mmio.removeExt(fp)+'.topo'):
                self.t[int(ln[0])] = (int(ln[1]), int(ln[2])) # {ordered id: (from swsid, to swsid)}
        else:
            print('error: sws .topo not found')
            quit()

        self.__buildSWS(hdem)

    def __buildSWS(self, hdem):        
        self.s = dict()
        ca = hdem.gd.cs**2
        pbar = tqdm(total=len(self.a))
        myProj = Proj("+proj=utm +zone=17N, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs")        
        for k,v in self.a.items():  
            pbar.update()          
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
            ss.ca = ca

            ss.km2 = sca / 1000 / 1000
            lg,ll = myProj(sx/n, sy/n, inverse=True)
            ss.ylat = ll
            ss.xlng = lg
            ss.elv = sz/n
            if sgn == 0 :
                ss.slp = 0.001
            else:
                ss.slp = sg/sgn
            ss.asp = (math.atan2(sax/n,say/n) + 2 * np.pi) % (2 * np.pi) # raven requires [0 to 2Pi] over [-Pi to Pi]
            ss.rchlen = math.sqrt(10) ##################################################### HARD CODED

            self.s[k] = ss            
        pbar.close()