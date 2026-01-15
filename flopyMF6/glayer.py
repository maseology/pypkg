

class Layer: # this version keeps the 2D array
    def __init__(self, top, bot):
        assert top.shape == bot.shape
        msk = (top>-999.) & (bot>-999.)
        self.top = top
        self.bot = bot
        self.msk = msk
        self.nnodes = int(msk.sum())
    
    def toplist(self): return list(self.top[self.msk])
    def botlist(self): return list(self.bot[self.msk])