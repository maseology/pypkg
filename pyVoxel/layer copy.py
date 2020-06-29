
import random
from pyGrid import vertex
from pyUnstruc import prism

class Layer:
    prsm = dict()

    def __init__(self, geom):        
        if type(geom) == vertex.VDEF:
            self.__buildVDEFrnd(geom)
        else:
            print("UNSTRUC.__init__ error")

    def __buildVDEFrnd(self,vdef):
        for k, cn in vdef.cellnodes.items():
            lcrd = list()
            for nid in cn: lcrd.append(vdef.nodecoord[nid])
            self.prsm[k] = prism.Prism(lcrd,random.random(),0.0)


