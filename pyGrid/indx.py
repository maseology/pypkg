
import os
import numpy as np
from pymmio import files as mmio
from pyGrid.definition import GDEF

class INDX:
    gd = None
    a = None

    def __init__(self,fp,gd=None):
        if gd == None:
            if os.path.exists(fp + ".gdef"):
                self.gd = GDEF(fp + ".gdef")
            elif os.path.exists(mmio.removeExt(fp)+".gdef"):
                self.gd = GDEF(mmio.removeExt(fp)+".gdef")
            else:
                print('INDX.__init__ grid definition cannot be found')
                quit()                
        else:
            self.gd = gd
        aa = np.fromfile(fp,int) #.reshape(gd.na)
        if len(aa) != len(self.gd.crc):
                print('INDX.__init__ incorrect grid definition')
                quit()
        self.x = dict(zip(self.gd.crc.keys(),aa))
        self.a = {}
        for k, v in self.x.items():
            self.a.setdefault(v, []).append(k)
        
    def saveAs(self,fp): self.gd.saveBinaryInt(fp,self.x)
