
import flopy
import matplotlib.pyplot as plt
from flopy.plot.styles import styles


def plotHeads(sim, nam, gd, fp=None):
    figure_size = (6, 8)

    with styles.USGSMap():
        gwf = sim.get_model(nam)

        # create MODFLOW 6 head object
        hobj = gwf.output.head()

        # create MODFLOW 6 cell-by-cell budget object
        cobj = gwf.output.budget()

        # extract heads
        head = hobj.get_data()
        vmin, vmax = 50, 550

        # extract specific discharge
        qx, qy, qz = flopy.utils.postprocessing.get_specific_discharge(
            cobj.get_data(text="DATA-SPDIS", kstpkper=(0, 0))[0], gwf
        )

        # Create figure for simulation
        extents = (gd.xul, gd.xul + gd.ncol * gd.cs, gd.yul - gd.nrow * gd.cs, gd.yul)
        fig = plt.figure(figsize=figure_size)
        ax = fig.add_subplot()
        ax.set_aspect("equal")
        ax.set_xlim(extents[:2])
        ax.set_ylim(extents[2:])

        fmp = flopy.plot.PlotMapView(model=gwf, ax=ax, layer=0, extent=extents)
        ax.get_xaxis().set_ticks([])
        fmp.plot_grid(lw=0.5)
        plot_obj = fmp.plot_array(head, vmin=vmin, vmax=vmax)
        fmp.plot_bc("DRN", color="green")
        # fmp.plot_bc("WEL", color="0.5")
        cv = fmp.contour_array(
            head, levels=[75, 100, 150, 200, 250, 300, 350], linewidths=0.5, colors="black"
        )
        plt.clabel(cv, fmt="%1.0f")
        fmp.plot_vector(qx, qy, normalize=True, color="0.75")
        title = 'layer one heads'
        styles.heading(heading=title, ax=ax)


        # create legend
        ax = fig.add_subplot()
        ax.set_xlim(extents[:2])
        ax.set_ylim(extents[2:])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["top"].set_color("none")
        ax.spines["bottom"].set_color("none")
        ax.spines["left"].set_color("none")
        ax.spines["right"].set_color("none")
        ax.patch.set_alpha(0.0)

        # ax = axes.flatten()[-2]
        # ax.axis("off")
        ax.plot(
            -10000, -10000, marker="s", ms=10, mfc="green", mec="green", label="Drain"
        )
        ax.plot(-10000, -10000, marker="s", ms=10, mfc="0.5", mec="0.5", label="Well")
        ax.plot(
            -10000,
            -10000,
            marker="$\u2192$",
            ms=10,
            mfc="0.75",
            mec="0.75",
            label="Normalized specific discharge",
        )
        ax.plot(-10000, -10000, lw=0.5, color="black", label=r"Head contour, $ft$")
        styles.graph_legend(ax, ncol=1, frameon=False, loc="center left")

        # plt.tight_layout(h_pad=-15)
        plt.subplots_adjust(top=0.9, hspace=0.5)

        # plot colorbar
        cax = plt.axes([0.525, 0.55, 0.35, 0.025])
        cbar = plt.colorbar(plot_obj, shrink=0.8, orientation="horizontal", cax=cax)
        cbar.ax.tick_params(size=0)
        cbar.ax.set_xlabel(r"Head, $ft$", fontsize=9)

        if fp is None:
            plt.show()
        else:
            fig.savefig(fp)

