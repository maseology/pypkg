
import numpy as np


def collectUBCbudgets(sim,nam,silent=True):
    gwf = sim.get_model(nam)
    cbc = gwf.output.budget()
    mds = [str(s)[2:-1].strip() for s in cbc.get_unique_record_names()] #['FLOW-JA-FACE', 'DATA-SPDIS', 'DRN', 'RIV', 'RCHA', 'CHD']
    if not silent: print(mds)

    def getflux(pak):
        flux_data = cbc.get_data(text=pak, totim=cbc.get_times()[-1])[0]

        if not silent: 
            print(pak)
            print(type(flux_data))
            print(flux_data.dtype.names) #('node', 'node2', 'q')
            print(flux_data[0:3])

        cids = flux_data['node']
        qs = flux_data['q']
        return cids, qs

    ubudgets = dict()
    ncpl = gwf.modelgrid.ncpl
    def add(nam):
        cids, qs = getflux(nam)
        flat = np.zeros(cbc.shape)
        flat[cids] = qs #* 86400. # convert to m3/d
        ubudgets[nam] = np.split(flat, np.cumsum(ncpl)[:-1])

    if 'DRN' in mds: add('DRN')
    if 'RIV' in mds: add('RIV')
    if 'RCH' in mds: add('RCH')
    if 'CHD' in mds: add('CHD')

    return ubudgets