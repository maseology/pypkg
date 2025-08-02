
import os
import math 
import numpy as np
from pymmio import files as mmio
from pyGrid.definition import GDEF

class REAL:
    gd = None
    a = None

    def __init__(self,fp,gd=None,dtyp=float):  #dtyp=np.dtype('float32')
        if gd == None:
            if os.path.exists(fp + ".gdef"):
                self.gd = GDEF(fp + ".gdef")
            elif os.path.exists(mmio.removeExt(fp)+".gdef"):
                self.gd = GDEF(mmio.removeExt(fp)+".gdef")
            elif os.path.exists(mmio.removeExt(fp)+".hdr"):
                self.gd = GDEF(mmio.removeExt(fp)+".hdr")                
            else:
                print('REAL.__init__ grid definition cannot be found')
                quit()                
        else:
            self.gd = gd
        
        aa = np.fromfile(fp,dtyp) #.reshape(gd.na)
        if fp[-3:]=='bil':
            if len(aa) != self.gd.nrow*self.gd.ncol:
                print('REAL.__init__ incorrect grid definition')
                print(str(len(aa)) + " " + str(self.gd.nrow*self.gd.ncol))
                quit()
            self.x = dict(zip(np.arange(self.gd.nrow*self.gd.ncol),aa))

        else:
            if len(aa) != len(self.gd.crc):
                    print('REAL.__init__ incorrect grid definition')
                    print(str(len(aa)) + " " + str(len(self.gd.crc)))
                    quit()
            self.x = dict(zip(self.gd.crc.keys(),aa))
            self.a = {}
            for k, v in self.x.items(): self.a.setdefault(v, []).append(k)
        
    def saveAs(self,fp): 
        if fp[-3:] in ["png","bmp"]:
            self.gd.saveBitmap(fp,self.x)
        else:
            self.gd.saveBinary(fp,self.x)

    def slopeAspectTarboton(self):
        #  ref: Tarboton D.G., 1997. A new method for the determination of flow directions and upslope areas in grid digital elevation models. Water Resources Research 33(2). p.309-319.
        #  triangular facets, ordered by steepest (assumes uniform cells)
        #  facets (slightly modified from Tarboton, 1997):
        #         \2|1/
        #         3\|/0
        #         --+--
        #         4/|\7
        #         /5|6\        
        re1 = [0, -1, -1, 0, 0, 1, 1, 0]
        ce1 = [1, 0, 0, -1, -1, 0, 0, 1]
        re2 = [-1, -1, -1, -1, 1, 1, 1, 1]
        ce2 = [1, 1, -1, -1, -1, -1, 1, 1]
        ac = [0., 1., 1., 2., 2., 3., 3., 4.]
        af = [1., -1., 1., -1., 1., -1., 1., -1.]
        atan1 = math.atan(1.)  #math.Atan(1.)
        cw = self.gd.cs
        hcw = math.sqrt(2 * cw**2)
        ncol = self.gd.ncol
        
        sxs, rgs = dict(), dict()
        for cid,e0 in self.x.items():
            if e0 < -998: 
                sxs[cid], rgs[cid] = 0., -9999.
                continue
            sx, rx, kx = 0., -9999, -1
            for k in range(8):
                c1, c2 = cid+re1[k]*ncol+ce1[k], cid+re2[k]*ncol+ce2[k]
                if not c1 in self.x: continue
                if not c2 in self.x: continue
                e1, e2 = self.x[c1], self.x[c2]
                if e1 < -998 or e2 < -998: continue
                if e1 > e0 and e2 > e0: continue

                s1 = (e0 - e1) / cw
                s2 = (e1 - e2) / cw
                r = math.atan2(s2,s1) # math.atan(s2 / s1)
                s = math.sqrt(s1**2 + s2**2)
                if r < 0:
                    r = 0
                    s = s1
                elif r > atan1:
                    r = atan1
                    s = (e0 - e2) / hcw

                if s > sx:
                    sx = s
                    rx = r
                    kx = k
            
            if kx < 0:
                sxs[cid], rgs[cid] = 0., -9999.
                continue

            rg = af[kx]*rx + ac[kx]*math.pi/2.
            if rg > math.pi: rg -= 2 * math.pi # [-pi,pi]

            sxs[cid], rgs[cid] = sx, rg

        return sxs, rgs