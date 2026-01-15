import struct
import numpy as np

class uLayer:
    
    def __init__(self, top, bot, constantHead, cellwidth, xul, yul, offset=0):
        assert top.shape == bot.shape
        msk = (top>-999.) & (bot>-999.) #& (top-bot>1e3) # excluding no cells where top==bottom
        self.top = top[msk]
        self.bot = bot[msk]
        constantHead[constantHead<=bot] = -9999.
        self.chbc = constantHead[msk] # constant head boundary
        self.cw = cellwidth # square cell width

        cids = np.arange(top.size, dtype=int).reshape(top.shape) # Cell ID: Row-major 2D grid 0-based cell id, every grid cell has a value
        acids = cids[msk] # list of active cids
        nnds = int(msk.sum()) # number of nodes
        nids = np.arange(nnds, dtype=int) # node ID: 0-based node id, only active cells are considered a node; nodes are cells removed from their grid association
        # cnxr = dict(zip(acids, nids)) # map of cid to nid

        # connectivity
        conn, ang, verts, cntrds = list(), list(), list(), list()
        gnids = np.ones(top.shape, dtype=int)*-9999
        gnids[msk] = nids+offset # node ID, assigned to 2D grid
        nr, nc = top.shape
        cd = [(-1, 0), (1, 0), (0, -1), (0, 1)] # cardinal directions
        ca = [180., 0., 90., 270.]              # direction angles

        cw2 = cellwidth/2 # uniform grid
        for i in range(nr):
            for j in range(nc):
                if not msk[i,j]: continue
                assert  cids[i,j] == i*nc+j # row-major

                lc, ag = [], []
                centroid = (j*cellwidth+cw2+xul, yul-i*cellwidth-cw2)
                cntrds.append(centroid)
                # verts.append([centroid[0]-cw2, centroid[1]+cw2]) # clockwise, always square cells
                # verts.append([centroid[0]+cw2, centroid[1]+cw2])
                # verts.append([centroid[0]+cw2, centroid[1]-cw2])
                # verts.append([centroid[0]-cw2, centroid[1]-cw2])
                verts.append([[centroid[0]-cw2, centroid[1]+cw2],
                              [centroid[0]+cw2, centroid[1]+cw2],
                              [centroid[0]+cw2, centroid[1]-cw2],
                              [centroid[0]-cw2, centroid[1]-cw2]])

                for ii in range(4):
                    di, dj = cd[ii]
                    ni, nj = i + di,j + dj
                    if 0 <= ni < nr and 0 <= nj < nc and msk[ni, nj]: 
                        lc.append(int(gnids[ni, nj]))
                        ag.append(ca[ii])
                conn.append(lc)
                ang.append(ag)

        self.nnodes = nnds
        self.nids = nids+offset # node IDs: id, only active cells are considered a node; nodes are cells removed from their grid association
        self.connections = conn # {nid: [laterally-connected node IDs]}
        self.connangles = ang # {nid: [angles to connected node IDs]}
        self.cids = acids
        self.mask = msk  # kept in original 2D shape
        self.vertices = verts
        self.centroids = cntrds

    def saveNodesIDs(self, fp):
        a = np.ones(self.mask.shape,dtype=np.int32)*-9999
        a[self.mask] = self.nids
        a.tofile(fp)
        

def getMF6(layers: list[uLayer]):
    def flat(list_of_lists): return [item for sublist in list_of_lists for item in sublist]
    
    disu_gridprops = {}
    disu_gridprops['nodes'] = sum([l.nnodes for l in layers])
    disu_gridprops['top'] = np.array(flat([l.top for l in layers]), dtype=np.float32)
    disu_gridprops['bot'] = np.array(flat([l.bot for l in layers]), dtype=np.float32)
    disu_gridprops['area'] = flat([[l.cw*l.cw]*l.nnodes for l in layers])

    def angtopar(angs, dz, cw, ca):
        ihc, cl12, hwva = [], [], []
        for a in angs:
            if a < 1.e29:
                ihc.append(1)
                cl12.append(cw/2)
                hwva.append(cw)       
            else:
                ihc.append(0)
                cl12.append(dz/2)
                hwva.append(ca)
        return ihc, cl12, hwva

    iac, ja, ihc, cl12, hwva, angldegx, vertices, cell2d = [], [], [], [], [], [], [], []
    nja, nvert, noffset, voffset = 0, 0, 0, 0
    vca = layers[0].cw**2 # Assumes all vertical faces areas is the same as the top layer resolution.
    for k, l in enumerate(layers):
        dz = l.top-l.bot
        for i, conn in enumerate(l.connections):
            ncon = len(conn)
            iac.append(ncon+1)
            nja += ncon+1
            cxy = l.centroids[i]
            v = [i*4+ii+voffset for ii in range(4)] + [i*4+voffset] # square cells, clockwise order
            a  = [i+noffset, cxy[0], cxy[1], 5] + v
            cell2d += [a]
            # iverts += [v]
            ja += [i+noffset] + conn
            iihc, icl12, ihwva = angtopar(l.connangles[i], dz[i], l.cw, vca)
            ihc += [k] + iihc
            cl12 += [0.] + icl12
            hwva += [0.] + ihwva
            angldegx += [1.e30] + l.connangles[i]
        
        # for i, xy in enumerate(l.vertices): vertices += [[i+voffset, xy[0], xy[1]]]
        for i, xys in enumerate(l.vertices): 
            for ii, xy in enumerate(xys): vertices += [[i*4+ii+voffset, xy[0], xy[1]]]

        nvert += len(l.vertices)*4
        noffset += l.nnodes
        voffset += len(l.vertices)*4

    disu_gridprops['iac'] = iac
    disu_gridprops['nja'] = nja
    disu_gridprops['ja'] = ja # ja has to be sorted
    disu_gridprops['ihc'] = ihc
    disu_gridprops['cl12'] = cl12
    disu_gridprops['hwva'] = hwva
    disu_gridprops['angldegx'] = angldegx
    disu_gridprops['nvert'] = nvert
    disu_gridprops['vertices'] = vertices
    disu_gridprops['cell2d'] = cell2d


    gridprops_ug = {}
    gridprops_ug['vertices'] = vertices
    # gridprops_ug['iverts'] = iverts
    gridprops_ug['cell2d'] = cell2d
    gridprops_ug['ncpl'] = [int(l.nnodes) for l in layers]
    # gridprops_ug['ncpl'] = [ncf, ncc, ncf]

    gridprops_ug['top'] = np.array(flat([l.top for l in layers]), dtype=np.float32) 
    gridprops_ug['botm'] = np.array(flat([l.bot for l in layers]), dtype=np.float32) 
    gridprops_ug['iac'] = iac
    gridprops_ug['ja'] = ja

    xc, yc = list(), list()
    for l in layers:
        for xy in l.centroids:
            xc.append(xy[0])
            yc.append(xy[1])

    gridprops_ug['xcenters'] = np.array(xc, dtype=np.float32)
    gridprops_ug['ycenters'] = np.array(yc, dtype=np.float32)

    return disu_gridprops, gridprops_ug

    # print('  saving pickles..')
    # with open(oprfx+'_DISU.pkl', 'wb') as f: pickle.dump(disu_gridprops, f, protocol=pickle.HIGHEST_PROTOCOL)
    # with open(oprfx+'_UGRID.pkl', 'wb') as f: pickle.dump(gridprops_ug, f, protocol=pickle.HIGHEST_PROTOCOL)
    # # with open(oprfx+'_DISU.pkl', 'rb') as f: disu_gridprops = pickle.load(f) # disu_gridprops
    # # with open(oprfx+'_UGRID.pkl', 'rb') as f: gridprops_ug = pickle.load(f) # gridprops_ug


def saveBinary(root, nam, disu_gridprops):
    iavert, javert = [], []
    for i, v in enumerate(disu_gridprops['cell2d']): 
        javert.extend(v[-5:])
        iavert.append(i*5)
    iavert.append(iavert[-1]+5)

    ia = [0]
    for i, c in enumerate(disu_gridprops['iac']): ia.append(ia[i]+c)

    with open(root+nam+'/'+nam+'.disu.bin'.format(nam), 'wb') as f:
        f.write(struct.pack('<i', disu_gridprops['nodes']))
        f.write(struct.pack('<i', disu_gridprops['nvert']))
        f.write(struct.pack('<i', disu_gridprops['nja']))
        f.write(struct.pack('<i', len(javert)))
        f.write(disu_gridprops['top'].tobytes())
        f.write(disu_gridprops['bot'].tobytes())
        f.write(np.array(ia, dtype=np.int32).tobytes())
        f.write(np.array(disu_gridprops['ja'], dtype=np.int32).tobytes())
        f.write(np.array([[v[1],v[2]] for v in disu_gridprops['vertices']], dtype=np.float32).tobytes())
        f.write(np.array(iavert, dtype=np.int32).tobytes())
        f.write(np.array(javert, dtype=np.int32).tobytes())