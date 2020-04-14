
class Extent:
    minx = 0.0
    maxx = 0.0
    miny = 0.0
    maxy = 0.0

    def __init__(self,MinX,MaxX,MinY,MaxY):
        self.minx = MinX
        self.maxx = MaxX
        self.miny = MinY
        self.maxy = MaxY

    def IsWithin(self,x,y,buf=0.0):
        if x < self.minx-buf: return False
        if x > self.maxx+buf: return False
        if y < self.miny-buf: return False
        if y > self.maxy+buf: return False
        return True