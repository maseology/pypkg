
import os
import numpy as np
from pymmio import files as mmio
from pyGrid.definition import GDEF

class INDX:
    gd = None
    a = None

    def __init__(self,fp,gd=None):
        # if mmio.getExtension(fp).lower()==".indx":
        if gd == None:
            if os.path.exists(fp + ".gdef"):
                self.gd = GDEF(fp + ".gdef")
            elif os.path.exists(mmio.removeExt(fp)+".gdef"):
                self.gd = GDEF(mmio.removeExt(fp)+".gdef")
            elif os.path.exists(mmio.removeExt(fp)+".hdr"):
                self.gd = GDEF(mmio.removeExt(fp)+".hdr")                
            else:
                print('INDX.__init__ grid definition cannot be found')
                quit()                
        else:
            self.gd = gd
        aa = np.fromfile(fp,np.int32) #.reshape(gd.na)

        # elif mmio.getExtension(fp).lower()==".bil":
        #     pass

        # else:
        #     print("unrecognized indx file type: "+fp)
        #     quit()

        if len(aa) == self.gd.nrow*self.gd.ncol:
            self.x = dict(zip(np.arange(self.gd.nrow*self.gd.ncol),aa))
        elif len(aa) == self.gd.nrow*self.gd.ncol/2:
            aa = np.fromfile(fp,np.int16).reshape(self.gd.act.shape)
            self.x = {}
            for k,v in self.gd.crc.items(): self.x[k] = aa[v]    
        elif len(aa) == self.gd.nrow*self.gd.ncol/4:
            aa = np.fromfile(fp,np.uint8).reshape(self.gd.act.shape)
            self.x = {}
            for k,v in self.gd.crc.items(): self.x[k] = aa[v]                        
        elif len(aa) != len(self.gd.crc):
            print('INDX.__init__ incorrect grid definition for '+fp)
            quit()
        else:
            self.x = dict(zip(self.gd.crc.keys(),aa)) # actives only
 
        self.a = {}
        self.x = {k:v for k, v in self.x.items() if v != -9999}
        for k, v in self.x.items():
            self.a.setdefault(v, []).append(k)
        
    def saveAs(self,fp): self.gd.saveBinaryInt(fp,self.x)
