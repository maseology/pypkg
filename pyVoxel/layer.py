
import random
import numpy as np
import statistics
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
                if type(geom[1]) == list: 
                    self.__buildGDEFlayered(geom)
                elif type(geom[1]) == np.ndarray:
                    self.__buildGDEFarray(geom)
                else:
                    print("Layer.__init__ error 000")
            elif type(geom[0]) == vertex.VDEF:
                self.__buildVDEFlayered(geom)
            else:
                print("Layer.__init__ error 00")
        elif type(geom) == vertex.VDEF:
            self.__buildVDEFrnd(geom)
        else:
            print("Layer.__init__ error END")

    def __buildVDEFrnd(self,vdef):
        for k, cn in vdef.cellnodes.items():
            lcrd = list()
            for nid in cn: lcrd.append(vdef.nodecoord[nid])
            self.prsms[k] = prism.Prism(lcrd,random.random(),-random.random())


    def __buildVDEFlayered(self,geom):
        vg = geom[0] # vertex grid 
        nly = geom[1] # number of layers/sub-divisions
        cnx = vg.adjacentCells() # only captures actives

        nc = len(vg.cellnodes)
        for ly in range(nly):
            for eid, nids in vg.cellnodes.items():
                pid = ly*nc + eid
                con = list()

                # build prism
                celltop = statistics.mean([vg.nodecoord[nid][2] for nid in nids])
                verts = [[vg.nodecoord[nid][0],vg.nodecoord[nid][1]] for nid in nids]           
                self.prsms[pid] = prism.Prism(verts,(1-ly/nly)*celltop,(1-(ly+1)/nly)*celltop)

                # lateral connections
                for c in cnx[eid]:
                    xid = ly*nc + c
                    con.append(xid)

                # vertical connections
                if ly > 0:
                    xid = (ly-1)*nc + eid
                    con.append(xid) # above
                else:
                    con.append(-1)
                if ly < nly-1:
                    xid = (ly+1)*nc + eid
                    con.append(xid) # below
                else:
                    con.append(-1)
                    
                self.prsms[pid].c = con

    def __buildGDEFlayered(self,geom):
        gd = geom[0] # grid definition
        nc = gd.ncol*gd.nrow
        dp = geom[1] # depths
        cnx = gd.adjacentCells() # only captures actives
        vg = vertex.VDEF(gd) # vertex grid  
        vg.RemoveCellsNonActives()
        da = 0.0
        for ly in range(len(dp)):
            for cid in gd.crc:
                pid = ly*nc + cid
                verts = list()
                con = list()

                # build prism
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

    def __buildGDEFarray(self,geom):
        gd = geom[0] # grid definition        
        top = geom[1]
        bot = geom[2]
        ly = geom[3]
        gd.setActives(top != 0)
        cnx = gd.adjacentCells() # only captures actives
        vg = vertex.VDEF(gd) # vertex grid  
        # vg.RemoveCellsNonActives()
        nc = gd.ncol*gd.nrow
        for cid, rc in gd.crc.items():
            pid = ly*nc + cid
            verts = list()
            con = list()

            # build prism
            for nid in vg.cellnodes[cid]: verts.append(vg.nodecoord[nid])                
            self.prsms[pid] = prism.Prism(verts,top.item(rc),bot.item(rc))

            # lateral connections
            for c in cnx[cid]:
                xid = ly*nc + c
                con.append(xid)

            # # vertical connections
            # if ly > 0:
            #     xid = (ly-1)*nc + cid
            #     con.append(xid) # above
            # if ly < len(dp)-1:
            #     xid = (ly+1)*nc + cid
            #     con.append(xid) # below

            self.prsms[pid].c = con
