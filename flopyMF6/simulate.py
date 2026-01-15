
import pickle
import numpy as np
import flopy
# from flopy.plot.styles import styles


def buildMonthlyPerioddata(nmonths=24, nstp_per_period=1):
    perlen = [30.*86400.]*nmonths
    nstp   = [nstp_per_period]*nmonths
    tsmult = [1.0]*nmonths
    return list(zip(perlen, nstp, tsmult))


def gridSS(root, nam, gd, idomain, top, botm, k11, k33, strt, rch, chd_spd = None, drn_spd = None, riv_spd = None, wel_spd = None, evt = None, icelltype=1, outer_maximum=100, perioddata=[[1., 1, 1.]]):

    print(f"  > numpy version: {np.__version__}")
    print(f"  > flopy version: {flopy.__version__}")

    istransient = len(perioddata)>1
    workspace = root
    # figs_path = root + "/figures"

    # Model parameters
    nlay = len(botm)  # Number of layers
    ncol = gd.ncol  # Number of columns
    nrow = gd.nrow  # Number of rows
    delr = gd.cs  # Column width ($ft$)
    delc = gd.cs  # Row width ($ft$)



    # ==================================================



    ws = workspace + '/' + nam
    sim = flopy.mf6.MFSimulation(sim_name=nam, sim_ws=ws, exe_name="mf6")
    flopy.mf6.ModflowTdis(sim, time_units='seconds', nper=len(perioddata), perioddata=perioddata)
    flopy.mf6.ModflowIms(
        sim,
        print_option="summary",
        complexity="complex",
        # csv_output_filerecord="bcf2ss.ims.csv",
        # # settings for "complex"
        # outer_dvclose=0.1,
        outer_maximum=outer_maximum,
        # under_relaxation="dbd",
        # under_relaxation_theta=0.8,
        # under_relaxation_kappa=1e-4,
        # under_relaxation_gamma=0.,
        # under_relaxation_momentum=0.,
        # backtracking_number=20,
        # backtracking_tolerance=1.05,
        # backtracking_reduction_factor=0.1,
        # backtracking_residual_limit=2e-3,
        # inner_maximum=500,
        # inner_dvclose=.1,
        # inner_rclose=.1,
        # linear_acceleration="BICGSTAB",
        # relaxation_factor=0.,
        # preconditioner_levels=5,
        # preconditioner_drop_tolerance=0.0001,        
        # number_orthogonalizations=2,
    )
    gwf = flopy.mf6.ModflowGwf(sim, modelname=nam, newtonoptions="newton", save_flows=True)
    flopy.mf6.ModflowGwfdis(
        gwf,
        length_units='meters',
        xorigin=gd.xul,
        yorigin=gd.yul-gd.nrow*gd.cs,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
        idomain=idomain,
    )
    npf = flopy.mf6.ModflowGwfnpf(
        gwf,
        icelltype=icelltype, # 0 means saturated thickness is held constant; >0 means saturated thickness varies with computed head when head is below the cell top
        k=k11,
        k33=k33,
        save_specific_discharge=True,
    )
    if istransient:
        flopy.mf6.ModflowGwfsto(
            gwf,
            pname="sto",
            save_flows=True,
            iconvert=1,
            ss= 1.e-6, #ss,
            sy= .2, #sy,
            # steady_state={0: True},
            # transient={1: True}
            transient={0: True}, # start straight to transient
        )

    flopy.mf6.ModflowGwfic(gwf, strt=strt)

    use_linear_ts = True
    if isinstance(rch,dict) & use_linear_ts & istransient: # transient recharge linear interpolation
        rcha = flopy.mf6.ModflowGwfrcha(gwf, recharge="TIMEARRAYSERIES rch_ts", timearrayseries=rch) # {time: rate}
        rcha.tas.time_series_namerecord = "rch_ts"
        rcha.tas.interpolation_methodrecord = "LINEAR"
    else:
        flopy.mf6.ModflowGwfrcha(gwf, recharge=rch)


    chd, drn, riv, wel = None, None, None, None
    if chd_spd is not None: chd = flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd_spd)
    if drn_spd is not None: drn = flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=drn_spd)
    if riv_spd is not None: riv = flopy.mf6.ModflowGwfriv(gwf, stress_period_data=riv_spd)
    if wel_spd is not None: wel = flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel_spd)
    if evt is not None: evt = flopy.mf6.ModflowGwfevta(gwf, rate=evt, surface=top, depth=1.)
    head_filerecord = f"{nam}.hds"
    budget_filerecord = f"{nam}.cbc"
    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=head_filerecord,
        budget_filerecord=budget_filerecord,
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )

    with open(root+nam+'/'+nam+'_sim.pkl', "wb") as f: pickle.dump(sim, f) 

    return sim, gwf, npf, chd, drn, riv, wel, evt



def unstructuredSS(root, nam, gridprops_ug, disu_gridprops, nlay, kh, strt, rch_spd, chd_spd = None, drn_spd = None, riv_spd = None, wel_spd = None, icelltype=1, outer_maximum=100, perioddata=[[1., 1, 1.]], skipvertices=False):

    print(f"  > numpy version: {np.__version__}")
    print(f"  > flopy version: {flopy.__version__}")

    istransient = len(perioddata)>1
    ugrid = flopy.discretization.UnstructuredGrid(**gridprops_ug)
    sim = flopy.mf6.MFSimulation(sim_name=nam, exe_name='mf6', version="mf6", sim_ws=root+nam)

    # Create the Flopy temporal discretization object
    tdis = flopy.mf6.modflow.mftdis.ModflowTdis(sim, pname="tdis", time_units="seconds", nper=len(perioddata), perioddata=perioddata)

    # Create the Flopy iterative model solver (ims) Package object
    ims = flopy.mf6.ModflowIms(
        simulation=sim, 
        print_option="summary", 
        complexity="complex", 
        # csv_output_filerecord="bcf2ss.ims.csv", 
        outer_maximum=outer_maximum,
    )

    # Create the Flopy groundwater flow (gwf) model object
    gwf = flopy.mf6.ModflowGwf(sim, modelname=nam, model_nam_file=nam+'.nam', newtonoptions='newton', save_flows=True)

    # build unstructured disu
    if skipvertices:
        del disu_gridprops['angldegx'] # these are needed when save_specific_discharge=True
        del disu_gridprops['nvert']
        del disu_gridprops['vertices']
        del disu_gridprops['cell2d']
    disu = flopy.mf6.modflow.ModflowGwtdisu(gwf, length_units='meters', **disu_gridprops)

    # Create the initial conditions package
    ic = flopy.mf6.modflow.mfgwfic.ModflowGwfic(gwf, pname="ic", strt=strt)

    # Create the node property flow package
    kuh = np.zeros(ugrid.nnodes, dtype=np.float32)
    kuv = np.zeros(ugrid.nnodes, dtype=np.float32)
    icelltype_nodes = np.ones(ugrid.nnodes, dtype=int)
    for i in range(nlay):
        rng = ugrid.get_layer_node_range(i)
        kuh[slice(*rng)] = kh[i]
        kuv[slice(*rng)] = kh[i]/10.
        icelltype_nodes[slice(*rng)] = icelltype[i] # 0 means saturated thickness is held constant; >0 means saturated thickness varies with computed head when head is below the cell top
    # npf = flopy.mf6.modflow.mfgwfnpf.ModflowGwfnpf(gwf, pname="npf", icelltype=laytypu, k=kuh, k33=kuv) #, save_specific_discharge=True)
    npf = flopy.mf6.modflow.mfgwfnpf.ModflowGwfnpf(gwf, pname="npf", icelltype=icelltype_nodes, k=kuh, k33=kuv)
    if not  skipvertices: npf.save_specific_discharge=True
    if istransient:
        flopy.mf6.ModflowGwfsto(
            gwf,
            pname="sto",
            save_flows=True,
            iconvert=1,
            ss= 1.e-6, #ss,
            sy= .2, #sy,
            # steady_state={0: True},
            # transient={1: True}
            transient={0: True}, # start straight to transient
        )

    # recharge
    use_linear_ts = True
    if isinstance(rch_spd,list) & use_linear_ts & istransient: # transient recharge linear interpolation
        # flopy.mf6.ModflowUtlts(
        #     gwf,
        #     time_series_namerecord="rch_ts",
        #     interpolation_methodrecord="LINEAR",
        #     timeseries=rch_spd,
        #     filename=nam+".rch.ts"
        # )
        rng = ugrid.get_layer_node_range(0)
        spd_list = [(i, "rch_ts") for i in range(rng[1])] #TIMESERIES
        # flopy.mf6.ModflowGwfrch(
        #     gwf,
        #     timeseries=nam+".rch.ts",
        #     stress_period_data={0: spd_list},
        #     pname="RCH"
        # )
        rch = flopy.mf6.ModflowGwfrch(gwf, stress_period_data={0: spd_list}, timeseries=rch_spd)
        rch.ts.time_series_namerecord = "rch_ts"
        rch.ts.interpolation_methodrecord = "LINEAR"
    else:
        flopy.mf6.modflow.mfgwfrch.ModflowGwfrch(gwf, pname="rch", stress_period_data=rch_spd)

    flopy.mf6.modflow.mfgwfchd.ModflowGwfchd(gwf, pname="chd", stress_period_data=chd_spd)

    if wel_spd is not None: flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel_spd)

    # rivers and drains
    flopy.mf6.modflow.mfgwfriv.ModflowGwfriv(gwf, pname="riv", stress_period_data=riv_spd)
    flopy.mf6.modflow.mfgwfdrn.ModflowGwfdrn(gwf, pname="drn", stress_period_data=drn_spd)

    # Create the output control package
    saverecord = [("HEAD", "ALL"), ("BUDGET", "ALL")]
    oc = flopy.mf6.modflow.mfgwfoc.ModflowGwfoc(
        gwf,
        pname="oc",
        saverecord=saverecord,
        head_filerecord=[nam+'.hds'],
        budget_filerecord=[nam+'.cbc'],
    )

    with open(root+nam+'/'+nam+'_sim.pkl', "wb") as f: pickle.dump(sim, f) 

    return sim