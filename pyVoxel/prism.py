
import numpy as np

class Prism:
    v = list() # vertices
    c = list() # connectivity
    t = 0.0    # top
    b = 0.0    # bottom

    def __init__(self, verts, top, bottom): #, connectivity=None):        
        if len(verts) < 3: print("prism.Prism error: vertically flat prism")
        if top <= bottom: print("prism.Prism error: flat prism (top <= bottom)")
        self.v = verts
        self.t = top
        self.b = bottom
        # if not connectivity is None: self.buildConnectivity(connectivity)

    # def buildConnectivity(self,connectivity):
    #     pass

    def Centroid(self):
        sx = 0.0
        sy = 0.0
        for xy in self.v:
            sx += xy[0]
            sy += xy[1]
        return [sx/len(self.v), sy/len(self.v), (self.t+self.b)/2]

    def Area(self):
        x = [i[0] for i in self.v]
        y = [i[1] for i in self.v]
        return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))        

