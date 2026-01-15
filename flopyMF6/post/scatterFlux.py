
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from OWRCMF6.flopyMF6.post.collectDischargeToSurface import collectDischargeToSurface


def scatterFlux(sim, nam, gd, obs_fluxfp, outpngfp, normalize=True):
    with open(obs_fluxfp, 'rb') as f: obs_flux = pickle.load(f)
    # print(obs_flux) # {cid: {name,baseflow,cids}}   built using prep/obs_flux.py

    qsurf = collectDischargeToSurface(sim,nam,gd)
    acell = float(gd.cs*gd.cs)
    f = 86400*365.24*1000.

    co, cs, cn = list(), list(), list()
    for cid, rec in obs_flux.items():
        if len(rec)==0:continue
        cn.append(rec['name'])
        r = list(rec['cids'])
        s = qsurf[r]
        s = s[s<0]
        a = float(len(r))*acell # basin area
        if normalize: # mm/yr
            cs.append(-float(np.sum(s))*f/a)
            co.append(rec['normbf']*f )
        else: # cms
            cs.append(-float(np.sum(s)))
            co.append(rec['normbf']*a)            
        
        

    df = pd.DataFrame({
        'baseflow': co,
        'simulated': cs,
        'name': cn,
    })
    # df = df[df['simulated']<2000]
    # print(df)

    df.plot.scatter(x='baseflow',y='simulated',zorder=2)
    plt.plot( [np.min(co), np.max(co)], [np.min(co), np.max(co)], color='red', linestyle='--', zorder=1 )
    if not outpngfp is None: plt.savefig(outpngfp, bbox_inches='tight')
    plt.show()
