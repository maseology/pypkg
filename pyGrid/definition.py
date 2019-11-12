
from scipy import spatial
import numpy as np
from scipy.interpolate import griddata
import math
from bitarray import bitarray
import mmio.bitarray as bt
from tqdm import tqdm


class gdef:
    pass

    def __init__(self, filepath):
        print(' loading', filepath)
        try:
            with open(filepath, 'rb') as f:
                self.xul=float(f.readline()) # UL corner
                self.yul=float(f.readline()) # UL corner
                self.rot=float(f.readline())
                if self.rot!=0.0: print(' rotated gdef currently unsupported')
                self.nrow=int(f.readline())
                self.ncol=int(f.readline())
                cs=f.readline()
                self.unif=False
                if chr(cs[0])=='U': self.unif=True
                if not self.unif: print(' variable cell size currently unsupported')
                self.cs=float(cs[1:])
                bact = f.read()
                if bact == b'':
                    self.active=False
                else:
                    ba = bitarray(endian='little')
                    ba.frombytes(bact)
                    # a = np.array(ba.tolist())[:self.nrow*self.ncol].reshape((self.nrow,self.ncol)) # active cell bitarray
                    # c = np.arange(0,self.nrow*self.ncol,1).reshape((self.nrow,self.ncol)) # cell id (2D) array
                    # # a2 = np.array(ba.tolist(),dtype=int)[:self.nrow*self.ncol].reshape((self.nrow,self.ncol))
                    # # a2.tofile("E:/tmp/gdef/t190501_active.indx")                    
                    # # print(np.sum(a), np.size(a))
                    # # print(a)
                    # # print(c)
                    # # print(c[a])
                    # self.act = c[a]
                    # a2 = np.array(ba.tolist(),dtype=int)[:self.nrow*self.ncol].reshape((self.nrow,self.ncol))
                    # print(a2)
                    # a2.tofile("M:/RDRR/met/ORMGP_50_cid.indx")    
                    self.act = np.array(ba.tolist())[:self.nrow*self.ncol].reshape((self.nrow,self.ncol)) # active cell bitarray to 2D boolean array
                    self.active=True

                # nl=f.readline()                
                # if len(nl)!=0: 
                #     # print(' active gdef currently unsupported')
                #     # self.active=False
                #     aa = []
                #     ba = bitarray.bitarray()               
                #     while len(nl)!=0:
                #         aa.extend(bt.tobits(nl))
                #         ba.frombytes(nl.encode('windows-1252'))
                #         print(ba)
                #         nl=f.readline()
                #     if sum(aa)>0:                        
                #         aa = aa[:self.nrow*self.ncol]
                #         print(sum(aa), len(aa))
                #         print(aa)
                #         np.asarray(aa).reshape((self.nrow,self.ncol)).tofile("E:/tmp/gdef/t190501_active.indx")
                #         self.active=True                                                           
                # else:
                #     self.active=False
                self.build()
        except FileNotFoundError:
            print(' grid definition file:',filepath,'not found.')
            quit()
        except Exception as err:
            print('error reading grid definition file:',filepath,'\n',err)
            quit()

    def build(self):         
        if self.active:
            self.ncell = np.sum(self.act)
            a = np.empty((self.nrow,self.ncol),dtype=int)
            a[self.act] = np.arange(0,self.ncell,1)
            self.rcc = a # row-col to active cell id            
        else:
            self.rcc = np.arange(0,self.nrow*self.ncol,1).reshape((self.nrow,self.ncol)) # row-col to cell id 
            self.ncell = self.nrow*self.ncol
            self.act = np.full((self.nrow,self.ncol),True,bool) # actives (all set to true for the moment) # dict.fromkeys(range(0,self.ncell), True) # {cid: True for cid in range(0,self.nrow*self.ncol)}         

        grc = np.array(np.meshgrid(range(self.nrow),range(self.ncol),indexing='ij')) 
        # self.crc = np.stack((grc[0, :, :],grc[1, :, :]),axis=2)[self.act].reshape(self.ncell,-1) # cell id to row-col 
        v = tuple(map(tuple, np.stack((grc[0, :, :],grc[1, :, :]),axis=2)[self.act].reshape(self.ncell,-1))) # cell id to row-col 

        c = np.arange(0,self.nrow*self.ncol,1).reshape((self.nrow,self.ncol)) # cell id (2D) array
        self.crc = dict(zip(c[self.act],v)) # dict of (active) cell id to row-col

        gco = np.array(np.meshgrid(range(self.ncol), range(self.nrow),indexing='xy'),float) # coordinate grid
        gco[0, :, :] *= self.cs  # cols/ec -- coordinate transformation (from https://bic-berkeley.github.io/psych-214-fall-2016/numpy_meshgrid.html)
        gco[1, :, :] *= -self.cs # rows/nc
        gco[0, :, :] += self.xul + self.cs/2. # cols/ec
        gco[1, :, :] += self.yul - self.cs/2. # rows/nc
        self.cco = np.stack((gco[0, :, :],gco[1, :, :]),axis=2) # row-col to coord (self.cco.reshape(self.ncell,-1) # converting np.array to list of coordinate list)

        # # the naive approach is very slow:
        # cid=0
        # for i in range(self.nrow):
        #     for j in range(self.ncol):
        #         self.act[cid]=True
        #         self.crc[cid]=(i,j)
        #         self.rcc[(i,j)]=cid
        #         self.cco[cid]=(self.xul+(j+0.5)*self.cs,self.yul-(i+0.5)*self.cs)
        #         cid+=1
        # self.ncell=cid

    def pointToRowCol(self,xy):
        # xy: tuple
        if self.rot != 0: pass # TODO: rotate point like p.Rotate(_rotation, New Cartesian.XY(_origin.X, _origin.Y), True)
        if xy[1] < self.yul-self.nrow*self.cs or xy[1] > self.yul or xy[0] < self.xul or xy[0] > self.xul+self.ncol*self.cs: return None #(-1,-1)
        x = self.xul
        y = self.yul
        ir = -1
        jc = -1

        while x < xy[0]:
            jc += 1
            x += self.cs
        while y > xy[1]:
            ir += 1
            y -= self.cs
        return (ir,jc)

    def pointToCellID(self,xy):
        p = self.pointToRowCol(xy)
        if p is not None: return self.rcc[p]

    def pointsToCellIDs(self,xys):
        # xys: dict of int,tuple
        dout = {}
        for k, v in xys.items():
            p = self.pointToRowCol(v)
            if p is not None: dout[k] = self.rcc[p] # != (-1,-1)
        return dout # pointID{cellID}

    ### IMPORT

    def LoadBinary(self,fp):
        try:
            return np.fromfile(fp,float).reshape((self.nrow,self.ncol))
        except Exception as error:
            print(error, '\n ', fp, 'is incompatible with this grid definition.')
            quit()
            
    def LoadIntBinary(self,fp):
        try:
            return np.fromfile(fp,int).reshape((self.nrow,self.ncol))
        except Exception as error:
            print(error, '\n ', fp, 'is incompatible with this grid definition.')
            quit()

    ### INTERPOLATION

    def nullMgrid(self):
        return(np.mgrid[self.xul+self.cs/2:self.xul+(self.ncol-1)*self.cs:complex(0,self.ncol), self.yul-self.cs/2:self.yul-(self.nrow-1)*self.cs:complex(0,self.nrow)]) # grid_x, grid_y (cell centered)

    def ThiessenPolygons(self,xys,fp):
        # this methods takes in a list of coordinates and saves an index grid of Thiessen (Voronoi) polygons to 'fp'
        # this differs from the methods below in that it creates a reference grid, not to interpolate values as needed
        # xys: dict of int,tuple
        grid_x, grid_y = self.nullMgrid()
        a = griddata(np.array(list(xys.values())), np.array(list(xys.keys())), (grid_x, grid_y), method='nearest') # 'linear' 'cubic'
        b = a.T
        b.tofile(fp)

    def buildInvDistanceWeights(self,xys,n,p=2.0):
        # xys: dict of int,tuple
        # p: weighting exponent; n: number of closest stations; r: search radius
        k = list(xys.keys()) # needed to index dict keys (in case they're not in any particular order)
        a = [list(v) for v in xys.values()] # converting list of tuples to list of lists
        g = self.cco.reshape(self.ncell,-1) # converting np.array to list of lists
        gd, gi = spatial.KDTree(a).query(g,k=n) # distance_upper_bound=r)        
        f = np.vectorize(lambda t: k[t]) # needed to remap KDTree index back to xys ids
        return f(gi), 1/gd**p # returns list of cell ids, list of point ids (per cell id), list of weights.

    def applyInterp(self,gi,gw,vals):
        # gi and gw created in buildInvDistanceWeights
        # vals is a dict of id,<value to interpolate>
        a=np.zeros(self.ncell)
        for c in range(self.ncell):
            nmr=0.0
            dnm=0.0
            for i in range(len(gi[c])):
                if gi[c][i] in vals:
                    nmr+=gw[c][i]*vals[gi[c][i]]
                    dnm+=gw[c][i]
            a[c]=nmr/dnm
        return a

    def applyInterpTheiss(self,gi,vals):
        # gi created in buildInvDistanceWeights
        # vals is a dict of id,<value to interpolate>
        a=np.zeros(self.ncell)
        for c in range(self.ncell):
            for i in range(len(gi[c])):
                if gi[c][i] in vals:
                    a[c]=vals[gi[c][i]]
                    break
        return a

    ### EXPORT

    def printActives(self,fp,dat=None):
        if dat is None:
            c = np.arange(0,self.nrow*self.ncol,1).reshape((self.nrow,self.ncol)) # cell id (2D) array
            a = c[self.act]
            a.tofile(fp)
        else:
            if type(dat)==list:
                with open(fp, "a") as fout:
                    pbar = tqdm(total=len(dat), desc='writing to ' + fp)
                    for a in dat:
                        pbar.update()
                        a[self.act].tofile(fout)
                    pbar.close()
            elif isinstance(dat,np.ndarray):
                dat[self.act].tofile(fp)
            else:
                print(' gdef.printActives does not support type: ' + str(type(dat)))
