
import numpy as np
from pyvtk import *

def PrismsToVTK(prsms, outputFP):
    id = list()
    pts = list()
    hex = list()    
    for k, p in prsms.items():
        id.append(k)
        v = np.array(p.v)
        t = np.full((v.shape[0],1),p.t)
        b = np.full((v.shape[0],1),p.b)
        tx = np.append(v, t, axis=1)
        bx = np.append(v, b, axis=1)
        ord = list(range(len(pts),len(pts) + 2*len(v)))
        pts.extend(l.tolist() for l in bx)
        pts.extend(l.tolist() for l in tx)        
        hex.append(ord)

    lns = list()
    for k, p in prsms.items():
        i0 = len(pts)
        pts.append(p.Centroid())
        for c in p.c:
            i1 = len(pts)
            id.append(i0+i1/10000)
            pts.append(prsms[c].Centroid())
            lns.append([i0,i1])

    fvtk = VtkData(UnstructuredGrid(pts, voxel=hex, line=lns), CellData(Scalars(id)))
    fvtk.tofile(outputFP, 'binary')

# def ConnectionsToVTK(prsms, outputFP):
#     pts = list()
#     lns = list()
#     for k, p in prsms.items():
#         i0 = len(pts)
#         pts.append(p.Centroid())
#         for c in p.c:
#             i1 = len(pts)
#             pts.append(prsms[c].Centroid())
#             lns.append([i0,i1])

#     fvtk = VtkData(UnstructuredGrid(pts, line=lns))
#     fvtk.tofile(outputFP, 'binary')


"""        
https://sourceforge.net/p/mayavi/mailman/message/6776236/

points = [[0,0,0],[1,0,0],[0,1,0],[1,1,1]]

vtk2 = VtkData( UnstructuredGrid(points, tetra=[[0,1,2,3]] ),
                CellData(Scalars([0.2]), Vectors([[0.0,0.0,1.0]])))
vtk2.tofile('test_cell')        
"""