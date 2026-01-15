import pickle
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from OWRCMF6.flopyMF6.post.collectDischargeToSurface import collectDischargeToSurface


def mapFlux(sim, nam, gd, obs_fluxfp, outpngfp, normalize=True):
    with open(obs_fluxfp, 'rb') as f: obs_flux = pickle.load(f)
    qsurf = collectDischargeToSurface(sim,nam,gd)
    acell = float(gd.cs*gd.cs)
    xs, ys, cn, ar, res = [], [], [], [], []
    f = 86400*365.24*1000.
    for _, rec in obs_flux.items():
        if len(rec)==0:continue
        xs.append(float(rec['long']))
        ys.append(float(rec['lat']))
        cn.append(rec['name'])
        ar.append(float(rec['area'])/1e6)
        r = list(rec['cids'])
        s = qsurf[r]
        s = s[s<0]
        a = float(len(r))*acell # basin area
        if normalize: # mm/yr
            sim = -float(np.sum(s))/a*f
            obs = rec['normbf']*f
        else: # cms
            sim = -float(np.sum(s))
            obs = (rec['normbf']*a)
        # res.append((sim - obs)/obs)
        res.append(sim - obs)


    # Basemap
    sflak = shapefile.Reader("E:/Sync/@gis/water/GreatLakes_UTM.shp")
    transformer = Transformer.from_crs("EPSG:26917", "EPSG:4326", always_xy=True)


    fig, ax = plt.subplots(figsize=(12, 8))
    patches = []

    # Loop through polygon shapes
    for shape_rec in sflak.shapeRecords():
        points = [transformer.transform(x, y) for x, y in shape_rec.shape.points]
        parts = list(shape_rec.shape.parts) + [len(points)]

        for i in range(len(parts) - 1):
            start, end = parts[i], parts[i + 1]
            polygon = Polygon(points[start:end], closed=True)
            patches.append(polygon)

    # Add polygons to plot
    poly_coll = PatchCollection(
        patches,
        facecolor='aqua',
        edgecolor='navy',
        linewidth=0.8
    )
    ax.add_collection(poly_coll)

    # model bound
    sfmdl = shapefile.Reader("M:/ORMGP-MF6/shp/model-domain_phase1-251003.shp")
    transformer = Transformer.from_crs("EPSG:3161", "EPSG:4326", always_xy=True)
    plgnmdl = [shape(s.__geo_interface__) for s in sfmdl.shapes()]
    plgnmdl[0] = transform(transformer.transform, plgnmdl[0])
    ax.plot(*plgnmdl[0].exterior.xy)


    # add gauges
    vmin, vmax = np.nanmin(res), np.nanmax(res)
    lim = max(abs(vmin), abs(vmax))
    norm = TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim)
    gag = ax.scatter(
        xs, ys,
        c=res, cmap='coolwarm', norm=norm, s=10*np.floor(np.log(ar)), zorder=5, label='Stream Gauges'
    )



    ax.autoscale()
    # ax.set_aspect('equal', 'box')
    ax.set_title("Flux residual by gauge", fontsize=14)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    # ax.set_xlim(-82, -76)
    # ax.set_ylim(42, 46)
    ax.set_xlim(-81, -77)
    ax.set_ylim(43, 45.5)
    # ax.legend()


    cbar = plt.colorbar(gag, shrink=0.8, pad=0.02, orientation='vertical', extend='both', ticks=[-lim,0,lim])
    cbar.set_label(r"Flux Residual, $mm/yr$", fontsize=9)

    if not outpngfp is None: plt.savefig(outpngfp, bbox_inches='tight')
    plt.show()
