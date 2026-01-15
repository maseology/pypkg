import flopy
from flopy.discretization import StructuredGrid
import numpy as np
import matplotlib.pyplot as plt

def plotLayer(gd, ndlayer, contour_levels = None):
    ibnd = np.zeros(gd.nrow*gd.ncol, dtype=int)
    ibnd[gd.act.reshape(gd.nrow*gd.ncol)>0]=1
    struct_grid = StructuredGrid(
        nlay=1, 
        delr=np.array(gd.ncol * [gd.cs]), 
        delc=np.array(gd.nrow * [gd.cs]), 
        xoff=gd.xul, 
        yoff=gd.yul-gd.nrow*gd.cs, 
        top=ndlayer.reshape((gd.nrow, gd.ncol)), 
        botm=ndlayer.reshape((1, gd.nrow, gd.ncol))-10., 
        idomain=ibnd.reshape((gd.nrow, gd.ncol))
    )

    top_sg = ndlayer.reshape((gd.nrow, gd.ncol))
    top_sg[top_sg<=-999.] = np.nan
    fig = plt.figure(figsize=(12,8))
    ax = fig.add_subplot()
    pmv = flopy.plot.PlotMapView(modelgrid=struct_grid)
    ax.set_aspect("equal")
    pltobj = pmv.plot_array(top_sg)
    # pmv.plot_grid(lw=0.25, color="0.5")
    if contour_levels is not None: pmv.contour_array(top_sg, levels=contour_levels, linewidths=0.3, colors="0.75")
    pmv.plot_inactive(color_noflow=".75")

    cbar = plt.colorbar(pltobj, shrink=0.8, orientation="vertical")
    cbar.ax.set_xlabel(r"Top of model, $masl$", fontsize=9)

    plt.show()