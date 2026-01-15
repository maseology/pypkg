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

def mapHeads(sim, nam, gd, obs_headsfp, outpngfp):
    obs_head = np.fromfile(obs_headsfp,dtype=np.float32).reshape(gd.shape())
    gwf = sim.get_model(nam)
    sim_head_all_layers = gwf.output.head().get_data()
    for sim_head in sim_head_all_layers:

        sim_head[sim_head>999] = np.nan
        obs_head[obs_head<-999] = np.nan
        resid = sim_head-obs_head
        p_low  = np.nanpercentile(resid, 2, )   # optional lower bound
        p_high = np.nanpercentile(resid, 98)  # upper bound
        resid[(resid < p_low) | (resid > p_high)] = np.nan


        # # plot raster
        # plt.figure(figsize=(8, 6))

        # # If the raster is single‑band (grayscale) you can set a colormap:
        # lim = max(abs(p_low), abs(p_high))
        # norm = TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim)
        # plt.imshow(resid, cmap='coolwarm', norm=norm, interpolation='nearest')

        # # Add a colorbar for reference
        # cbar = plt.colorbar(shrink=0.8, pad=0.02, orientation='vertical', extend='both', ticks=[-lim,0,lim])
        # cbar.set_label(r"Head Residual, $m$")

        # # Optional: add title, axis labels
        # plt.title('Raster visualization')
        # plt.xlabel('Column index')
        # plt.ylabel('Row index')

        # plt.tight_layout()
        # plt.show()


        # plot points

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

        xs = gd.cco[:,:,0][~np.isnan(resid)]
        ys = gd.cco[:,:,1][~np.isnan(resid)]
        xs, ys = transformer.transform(xs, ys)

        resid = resid[~np.isnan(resid)]
        # ax.hist(resid, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
        # plt.show()

        lim = max(abs(p_low), abs(p_high))
        norm = TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim)
        gag = ax.scatter(
            xs, ys,
            # c=resid, cmap='coolwarm', norm=norm, s=resid/10, zorder=5, label='Stream Gauges'
            c=resid, cmap='coolwarm', norm=norm, s=1, zorder=5, label='Stream Gauges'
        )


        ax.autoscale()
        # ax.set_aspect('equal', 'box')
        ax.set_title("Head residual", fontsize=14)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        # ax.set_xlim(-82, -76)
        # ax.set_ylim(42, 46)
        ax.set_xlim(-81, -77)
        ax.set_ylim(43, 45.5)
        # ax.legend()

        cbar = plt.colorbar(gag, shrink=0.8, pad=0.02, orientation='vertical', extend='both', ticks=[-lim,0,lim])
        cbar.set_label(r"Head Residual, $m$", fontsize=9)

        # if not outpngfp is None: plt.savefig(outpngfp, bbox_inches='tight')
        plt.show()
