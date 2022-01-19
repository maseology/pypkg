

class VDEF:
    nodecoord = dict()
    cellnodes = dict() # references nodes connected to each cell
    nodecells = dict() # references cells associated with each node

    def __init__(self, gdef=None):
        if gdef is None: return

        #  collects cell IDs surrounding grid intersections
        #  EXAMPLE: 4x5 cells (5x6 nodes)
        #   0---1---2---3---4---5
        #   | 0 | 1 | 2 | 3 | 4 |
        #   6---7---8---9--10--11
        #   | 5 | 6 | 7 | 8 | 9 |
        #  12--13--14--15--16--17
        #   | 10| 11| 12| 13| 14|
        #  18--19--20--21--22--23
        #   | 15| 16| 17| 18| 19|
        #  24--25--26--27--28--29

        # grid node coordinates        
        self.gd = gdef
        for i in range(gdef.nrow):
            for j in range(gdef.ncol):
                # if not gdef.act[i][j]: continue
                self.nodecoord[len(self.nodecoord)] = [gdef.CellLeft(i,j), gdef.CellTop(i,j)]
                if j == gdef.ncol-1: self.nodecoord[len(self.nodecoord)] = [gdef.CellRight(i,j), gdef.CellTop(i,j)]

        for j in range(gdef.ncol):
            # if not gdef.act[gdef.nrow-1][j]: continue
            self.nodecoord[len(self.nodecoord)] = [gdef.CellLeft(i,j), gdef.CellBottom(i,j)]
            if j == gdef.ncol-1: self.nodecoord[len(self.nodecoord)] = [gdef.CellRight(i,j), gdef.CellBottom(i,j)]

        # Build        
        cid = 0
        for i in range(gdef.nrow):
            for j in range(gdef.ncol):
                # p2---p3   y
                #  | c |    |        set to VTK standard
                # p0---p1   0---x
                nds = list()
                nds.append(cid + i + gdef.ncol + 1) # p0
                nds.append(cid + i + gdef.ncol + 2) # p1
                nds.append(cid + i) # p2
                nds.append(cid + i + 1) # p3
                self.cellnodes[cid] = nds
                cid += 1

        for nid in self.nodecoord:
            self.nodecells[nid] = [-1, -1, -1, -1] # initialize (-1 for no adjacent cell)

        for cid in self.cellnodes:
            # 2---1
            # | n |
            # 3---0
            self.nodecells[self.cellnodes[cid][0]][1] = cid
            self.nodecells[self.cellnodes[cid][1]][2] = cid
            self.nodecells[self.cellnodes[cid][2]][0] = cid
            self.nodecells[self.cellnodes[cid][3]][3] = cid

    def adjacentCells(self, cardinalOnly=True):
        d = dict()
        if cardinalOnly:
            for eid, nids in self.cellnodes.items():
                dd = dict()
                for nid in nids:
                    for eid2 in self.nodecells[nid]:
                        if eid2==-1: continue
                        if eid2==eid: continue
                        if not eid2 in dd: dd[eid2] = 1
                        dd[eid2] += 1                           
                l = list()
                for eid2, cnt in dd.items():
                    if cnt <3: continue
                    l.append(eid2)
                d[eid] = l
        else:
            for eid, nids in self.cellnodes.items():
                l = list()
                for nid in nids: l.extend(self.nodecells[nid])
                l = list(set(l)) # get unique
                l = list(filter((eid).__ne__,l)) # safer than l.remove(eid)
                l = list(filter((-1).__ne__,l))
                d[eid] = l
        return d

    def RemoveCells(self,cells):
        if type(cells) is int: cells = [cells]

        def f0(cid):
            if cid in self.cellnodes:
                l = self.cellnodes[cid]
                del self.cellnodes[cid]
                return l

        nrem = list(map(f0,cells))
        nrem = [item for sublist in nrem for item in sublist] # flatten list see:https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
        nrem = list(set(nrem)) # distinct nodes

        # nrem = list() # nodes to be removed
        # for cid in cells:
        #     if not cid in self.cellnodes: continue
        #     nrem.extend(self.cellnodes[cid])
        #     del self.cellnodes[cid]

        def f1(nid):
            lst = list(map(f2,self.nodecells[nid]))            
            self.nodecells[nid] = lst
            if len(lst) == 0 or all(cid == -1 for cid in lst): return nid

        def f2(cid):
            if cid in cells: return -1
            return cid

        rem2 = list(map(f1,nrem))

        # rem2 = list()
        # for nid in list(set(nrem)):            
        #     lst = list()
        #     for cid in self.nodecells[nid]:
        #         if cid in cells:
        #             lst.append(-1)
        #         else:
        #             lst.append(cid)
            
        #     if len(lst) == 0 or all(cid == -1 for cid in lst): rem2.append(nid)
        #     self.nodecells[nid] = lst
        
        if len(rem2) > 0:
            for nid in list(set(rem2)):
                del self.nodecells[nid]
                del self.nodecoord[nid]

    def RemoveCellsNonActives(self):
        rem = list()
        for i in range(self.gd.nrow):
            for j in range(self.gd.ncol):
                if not self.gd.act[i][j]: rem.append(self.gd.CellID(i,j))
        if len(rem) > 0: self.RemoveCells(rem)

    # def Copy(self,translateZ=0.0):
    #     vdef = VDEF()
    #     vdef.cellnodes = self.cellnodes.copy()
    #     vdef.nodecells = self.nodecells.copy()
    #     vdef.nodecoord = self.nodecoord.copy()
    #     for k in vdef.nodecoord:
    #         vdef.nodecoord[k] = (vdef.nodecoord[k][0],vdef.nodecoord[k][1],vdef.nodecoord[k][2] + translateZ)
    #     return vdef

def ReadAH3(fp):
    vg = VDEF()

    # read file
    xyz = list()
    elm = list()
    with open(fp, "r") as f:
        nps = int(f.readline())
        for _ in range(nps): xyz.append([float(item) for item in f.readline().split()])
        epl = int(f.readline())
        for _ in range(epl): elm.append([int(item)-1 for item in f.readline().split()]) # zero-based

    # Build
    nid = 0
    for c in xyz:
        vg.nodecoord[nid] = c
        vg.nodecells[nid] = [-1, -1, -1, -1] # initialize (-1 for no adjacent cell)
        nid += 1

    eid = -1
    for v in elm:
        eid += 1
        if len(v)==4:
            vg.cellnodes[eid] = v
            # p2---p3   y
            #  | c |    |        set to VTK standard
            # p0---p1   0---x
            vg.nodecells[vg.cellnodes[eid][0]][1] = eid
            vg.nodecells[vg.cellnodes[eid][1]][2] = eid
            vg.nodecells[vg.cellnodes[eid][2]][0] = eid
            vg.nodecells[vg.cellnodes[eid][3]][3] = eid
            # 2---1
            # | n |
            # 3---0            
        else:
            print('---------------------- TODO')

    return vg