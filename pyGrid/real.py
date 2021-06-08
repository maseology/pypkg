
import os
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
            else:
                print('REAL.__init__ grid definition cannot be found')
                quit()                
        else:
            self.gd = gd
        
        aa = np.fromfile(fp,dtyp) #.reshape(gd.na)
        if len(aa) != len(self.gd.crc):
                print('REAL.__init__ incorrect grid definition')
                print(str(len(aa)) + " " + str(len(self.gd.crc)))
                quit()
        self.x = dict(zip(self.gd.crc.keys(),aa))
        self.a = {}
        for k, v in self.x.items():
            self.a.setdefault(v, []).append(k)
        
    def saveAs(self,fp): self.gd.saveBinary(fp,self.x)
