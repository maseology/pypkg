
import random
from pyGrid import definition, vertex
from pyVoxel import prism

"""
Layer requires prisms with known lateral connectivity assumed conduct accross 100% of the cell's face (contiguity)
"""

class Layer:
    prsms = dict()

    def __init__(self, geom):        
        if type(geom) == tuple:
            if type(geom[0]) == definition.GDEF:
                if not type(geom[1]) == list: print("UNSTRUC.__init__ error 000")
                self.__buildVDEFlayered(geom)
            else:
                print("UNSTRUC.__init__ error 00")
        elif type(geom) == vertex.VDEF:
            self.__buildVDEFrnd(geom)
        else:
            print("UNSTRUC.__init__ error END")

    def __buildVDEFrnd(self,vdef):
        for k, cn in vdef.cellnodes.items():
            lcrd = list()
            for nid in cn: lcrd.append(vdef.nodecoord[nid])
            self.prsms[k] = prism.Prism(lcrd,random.random(),-random.random())

    def __buildVDEFlayered(self,geom):
        gd = geom[0] # grid definition
        nc = gd.ncol*gd.nrow
        dp = geom[1] # depths
        cnx = gd.adjacentCells() # only captures actives
        vg = vertex.VDEF(gd) # vertex grid  
        vg.RemoveCellsNonActives()
        pid = 0
        da = 0.0
        for ly in range(len(dp)):
            for cid in gd.crc:
                pid = ly*nc + cid
                verts = list()
                con = list()
                for nid in vg.cellnodes[cid]: verts.append(vg.nodecoord[nid])                
                self.prsms[pid] = prism.Prism(verts,da,da-dp[ly])

                # lateral connections
                for c in cnx[cid]:
                    xid = ly*nc + c
                    con.append(xid)

                # vertical connections
                if ly > 0:
                    xid = (ly-1)*nc + cid
                    con.append(xid) # above
                if ly < len(dp)-1:
                    xid = (ly+1)*nc + cid
                    con.append(xid) # below

                self.prsms[pid].c = con
            da -= dp[ly]
        pass

