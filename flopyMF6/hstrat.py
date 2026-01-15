
import numpy as np

class HSTRAT:

    def __init__(self, gd, top, botms, idomain):
        if type(top) != np.ndarray: print('HSTRAT WTF1')
        # print(type(top), top.shape)
        # print(type(botms), botms.shape)
        # print(type(idomain), idomain.shape)
        
        self.gd = gd
        self.nlay = botms.shape[0]
        self.top = top
        self.botm = botms
        self.idomain = idomain

    def shape(self): return self.botm.shape

    def pointToRowColLay(self,pnt):
        ij = self.gd.pointToRowCol(pnt)
        if ij is None: return None
        i,j = ij
        if pnt[2]>self.top[i,j]: return (i,j,0)
        if pnt[2]<self.botm[-1,i,j]: return (i,j,self.nlay-1)
        for k in range(self.nlay):
            if pnt[2]>=self.botm[k,i,j]: break
        return (i,j,k)

