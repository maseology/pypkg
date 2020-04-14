
import os
import numpy as np
from pymmio import files as mmio
from pyGrid.definition import gdef

class indx:
    gd = None
    a = None

    def __init__(self,fp,gd=None):
        if gd == None:
            if os.path.exists(fp + ".gdef"):
                self.gd = gdef(fp + ".gdef")
            elif os.path.exists(mmio.removeExt(fp)+".gdef"):
                self.gd = gdef(mmio.removeExt(fp)+".gdef")
            else:
                print('grid definition cannot be found')
                quit()                
        else:
            self.gd = gd
        aa = np.fromfile(fp,int) #.reshape(gd.na)
        aaa = dict(zip(gd.crc.keys(),aa))
        self.a = {}
        for k, v in aaa.items():
            self.a.setdefault(v, []).append(k)
        


