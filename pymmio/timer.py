
from datetime import timedelta
from timeit import default_timer as timer

class mmtimer:    
    b0 = None
    i0 = None

    def __init__(self):
        t = timer()
        self.b0 = t
        self.i0 = t

    def lap(self,msg=""):
        t = timer()
        lap = str(timedelta(seconds=round(t - self.i0,0)))
        self.i0 = t
        if len(msg)>0:
            print(msg +' >> '+lap)
        else:
            print('TOTAL LAP TIME: ' + lap)

    def end(self):
        endtime = str(timedelta(seconds=round(timer() - self.b0,0)))
        print('TOTAL ELAPSED TIME: ' + endtime)