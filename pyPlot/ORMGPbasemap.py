
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

import shapefile
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer


def basemap(xlim=None, ylim=None):
    fig, ax = plt.subplots(figsize=(12, 8))
    sflak = shapefile.Reader("E:/Sync/@gis/water/GreatLakes_UTM.shp")
    transformer = Transformer.from_crs("EPSG:26917", "EPSG:4326", always_xy=True)

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
        facecolor='#2B5BB5', #'aqua',
        edgecolor='#2B5BB5', #'#0F203F', #'navy',
        linewidth=0.8
    )
    ax.add_collection(poly_coll)

    # domain boundary
    bndry = shapefile.Reader("M:/ORMGP-MF6/shp/model-domain_phase1-251003.shp")
    transformer = Transformer.from_crs("EPSG:3161", "EPSG:4326", always_xy=True)

    plgnbndry = [shape(s.__geo_interface__) for s in bndry.shapes()]
    plgnbndry[0] = transform(transformer.transform, plgnbndry[0])
    ax.plot(*plgnbndry[0].exterior.xy, color='black', linestyle='--', alpha=0.85, linewidth=1)

    # properties/formatting
    ax.autoscale()
    # ax.set_aspect('equal', 'box')    
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    if (xlim is not None) & (ylim is not None):
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        # ax.set_xlim(-81, -77)
        # ax.set_ylim(43, 45.5)

    return fig, ax