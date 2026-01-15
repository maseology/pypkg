
import numpy as np


def collectDischargeToSurface(sim,nam,gd,silent=True):
    gwf = sim.get_model(nam)
    cbc = gwf.output.budget()
    mds = [str(s)[2:-1].strip() for s in cbc.get_unique_record_names()] #['FLOW-JA-FACE', 'DATA-SPDIS', 'DRN', 'RIV', 'RCHA', 'CHD']

    if not silent: print(mds)
    def getflux(pak):
        flux_data = cbc.get_data(text=pak, totim=cbc.get_times()[-1])[0]

        if not silent: 
            print(type(flux_data))
            print(flux_data.dtype.names) #('node', 'node2', 'q')
            print(flux_data[0:3])

        cids = flux_data['node']
        qs = flux_data['q']
        return cids, qs

    # aggregate all layer 1 fluxes (assumed) to grid
    aflat = np.zeros(gd.shape).flatten()
    if 'DRN' in mds:
        cids, qs = getflux('DRN')
        aflat[cids] += qs #* 86400. # convert to m3/d
    if 'RIV' in mds:
        cids, qs = getflux('RIV')
        aflat[cids] += qs #* 86400.
    if 'RCHA' in mds:
        cids, qs = getflux('RCHA')
        qs[qs>0] = 0
        aflat[cids] += qs #* 86400.
    # aflat.tofile('M:/ORMGP-MF6/ORMGP1lay/ORMGP1lay_qSurf.bil')
    return aflat