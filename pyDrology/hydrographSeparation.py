import math
from scipy.signal import lfilter
import numpy as np
from scipy.signal.signaltools import lfilter
from scipy.stats import linregress
from datetime import timedelta
# import matplotlib.pyplot as plt


########################################################
# automated extraction of the baseflow recession coefficient k as in Linsley, Kohler, Paulhus (1975) pg.230
# ref: Linsley, R.K., M.A. Kohler, J.L.H. Paulhus, 1975. Hydrology for Engineers 2nd ed. McGraw-Hill. 482pp.
########################################################
def recessionCoef(df):
    # collect recession dates
    d = df.to_dict('index')
    x, y = [], []
    for k,v in d.items():
        k1 = k + timedelta(days=1)
        if k1 in d: 
            if v['Val'] > d[k1]['Val']: 
                x.append(d[k1]['Val'])
                y.append(v['Val'])   
    # xt = x.copy()
    # yt = y.copy()

    while True:
        lnreg = linregress(x,y)
        # print(lnreg)
        if lnreg.rvalue > 0.995: break
        rem = []
        for i in range(len(x)): 
            if y[i] > lnreg.slope*x[i]: rem.append(i)
        if len(rem)==len(x): break
        for i in sorted(rem, reverse = True):
            del x[i]
            del y[i]

    x2 = np.vstack([x, np.zeros(len(x))]).T # x needs to be a column vector instead of a 1D vector for this https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html
    a, _,_,_ = np.linalg.lstsq(x2, y, rcond=None) 
    # print(1/a[0]) # =k
    # plt.scatter(xt, yt, alpha=0.5)    
    # plt.plot(x2,a*x2,"r", alpha=0.75)
    # plt.xlabel("$Q_t$")
    # plt.ylabel("$Q_{t-1}$")
    # plt.show()
    return 1/a[0]


########################################################
# recession days
# time (in days) after peak discharge from which quick flow ceases and total flow is entirely slow flow
# ref: Linsley, R.K., M.A. Kohler, J.L.H. Paulhus, 1975. Hydrology for Engineers 2nd ed. McGraw-Hill. 482pp.
########################################################
def Ndays(careaKM2): return 0.827 * careaKM2 ** 0.2


########################################################
# digital filter methods of automatic baseflow separation
########################################################
def digitalFilter(v, a1, b0, b1, nPasses=1):
    if nPasses <= 1: return np.minimum(v, lfilter([b0,b1], [1.0,-a1], v, axis=0))
    f = v
    for i in range(nPasses):
        if (i+1) % 2 == 0: f = np.flip(f)
        f = lfilter([b0,b1], [1.0,-a1], f, axis=0)
        if (i+1) % 2 == 0: f = np.flip(f)
        f = np.minimum(v, f)
    return np.minimum(v,f)



########################################################
# UKIH
########################################################
# Institute of Hydrology, 1980. Low Flow Studies report. Wallingford, UK.
# Piggott, A.R., S. Moin, C. Southam, 2005. A revised approach to the UKIH method for the calculation of baseflow. Hydrological Sciences Journal 50(5): 911-920.
def ukih(v, N):
    vvv = v
    for i in range(N):
        sukih = "o" + str(i)
        s = v.shift(-i, "D").rolling(str(N)+'D').min()
        s.rename(columns={'Val': sukih}, inplace=True)

        vv = v.merge(s, on='Date')
        vv[sukih] = np.where(vv['Val']==vv[sukih], vv[sukih], np.NaN) # turning point
        vv[sukih].interpolate(method = 'linear', inplace = True) # interpolate
        vvv = vvv.merge(vv[sukih], on='Date')

    vvv['n'] = vvv.iloc[:,-N:].min(axis=1)
    vvv['x'] = vvv.iloc[:,-N:].max(axis=1)
    vvv['m'] = vvv.iloc[:,-N:].median(axis=1)

    vvv['sweepingMin'] = vvv[['Val','n']].min(axis=1)
    vvv['sweepingMax'] = vvv[['Val','x']].min(axis=1)
    vvv['sweepingMedian'] = vvv[['Val','m']].min(axis=1)

    vvv.drop(vvv.iloc[:, 1:(N+4)], axis=1, inplace=True)

    # vvv[vvv.index.year>2015].plot(figsize=(20,10))
    # print(vvv)
    return vvv


########################################################
# HYSEP
########################################################
# Sloto, R.A. and M.Y. Crouse, 1996. HYSEP: A Computer Program for Streamflow Hydrograph Separation and Analysis U.S. Geological Survey Water-Resources Investigations Report 96-4040.
def hysep(v, N):
    twoNs =  2 * math.floor(N) + 1 # nearest odd integer
    twoNsm1 = (twoNs-1)/2

    s = v.rolling(str(twoNs)+'D').min()[twoNs-1::twoNs]
    s.rename(columns={'Val': 'FI'}, inplace=True)
    vv = v.merge(s, how='left', on='Date') 
    vv['FI'].fillna(method="bfill", inplace=True)

    s = v.rolling(str(twoNsm1)+'D').min()
    s.rename(columns={'Val': 'SI'}, inplace=True)
    vv = vv.merge(s, how='left', on='Date')

    vv['LM'] = np.where(vv['Val']==vv['SI'], vv['SI'], np.NaN) # turning point
    vv['LM'].interpolate(method = 'linear', inplace = True) # interpolate
    vv['LM'] = vv[['Val','LM']].min(axis=1)

    # print(vv)
    # vv[vv.index.year>2015].plot(figsize=(20,10))
    return vv


########################################################
# PART
########################################################
# Rutledge, A.T., 1998. Computer Programs for Describing the Recession of Ground-Water Discharge and for Estimating Mean Ground-Water Recharge and Discharge from Streamflow Records-Update, Water-Resources Investigation Report 98-4148.
def part(v, N, logdecline = .1):
    vvv = v.copy()
    for antereq in range(3):
        Npart = math.floor(N)+antereq # "largest integer that is less than the result of equation 1"
        arr = 'bf-'+str(Npart)
        vv = v.copy()

        s = v.rolling(str(Npart)+'D').min()
        s.rename(columns={'Val': arr}, inplace=True)
        vv = vv.merge(s, how='left', on='Date')
        vv[arr][vv['Val'] > vv[arr]] = np.NaN

        vv['o1'] = np.log10(vv['Val'])
        vv['o2'] = -vv['o1'].diff()

        vv[arr][vv['o2'] <0] = np.NaN
        
        vv[arr][vv['o2'] > logdecline] = np.NaN

        vv[arr].interpolate(method = 'linear', inplace = True) # interpolate
        
        vv[arr] = vv[['Val',arr]].min(axis=1)

        # print(vv)
        # vv[vv.index.year>2015].plot(figsize=(20,10))
        vvv = vvv.merge(vv[arr], how='left', on='Date')

    # print(vvv)
    # vvv[vvv.index.year>2015].plot(figsize=(20,10))
    return vvv



########################################################
# the "Clarifica" technique (a.k.a. Graham method); named in (Clarifica, 2002) as a "forward and backward-step averaging approach."
########################################################
def clarifica(v):
    # ref: Clarifica Inc., 2002. Water Budget in Urbanizing Watersheds: Duffins Creek Watershed. Report prepared for the Toronto and Region Conservation Authority.
    # Clarifica method baseflow, 5-day avg running, 6-day min running   
    s = v.rolling('6D').min() # 6-day running minimum discharge   
    s = s.rolling('5D').mean().shift(-1, "D") # 5-day running average (3 days previous, 1 day ahead)
    return np.minimum(np.asarray(v),np.asarray(s))


########################################################
# returns grand estimate of baseflow
########################################################
def estimateBaseflow(df, dakm2, k):
    dfo = df.copy()

    ###
    # DIGITAL FILTER
    nPass = 1
    # Lyne, V. and M. Hollick, 1979. Stochastic time-variable rainfall-runoff modelling. Hydrology and Water Resources Symposium, Institution of Engineers Australia, Perth: 89-92.
    #  k <- 0.925 # Ranges from 0.9 to 0.95 (Nathan and McMahon, 1990).  
    a = k
    b = (1-k)/2
    c = (1-k)/2
    nPass = 3 #  3 passes commonly used (Chapman, 1999)
    dfo['LynnHollick'] = digitalFilter(df[['Val']].to_numpy(),a,b,c,nPass)

    # Chapman, T.G., 1991. Comment on the evaluation of automated techniques for base flow and recession analyses, by R.J. Nathan and T.A. McMahon. Water Resource Research 27(7): 1783-1784
    a = (3*k-1)/(3-k)
    b = (1-k)/(3-k)
    c = (1-k)/(3-k)
    dfo['Chapman91'] = digitalFilter(df[['Val']].to_numpy(),a,b,c,1)

    # Chapman, T.G. and A.I. Maxwell, 1996. Baseflow separation - comparison of numerical methods with tracer experiments. Institute Engineers Australia National Conference. Publ. 96/05, 539-545.
    a = k/(2-k)
    b = (1-k)/(2-k)
    c = 0
    dfo['ChapmanMaxwell'] = digitalFilter(df[['Val']].to_numpy(),a,b,c,1)

    # Boughton & Eckhardt
    # Boughton, W.C., 1993. A hydrograph-based model for estimating the water yield of ungauged catchments. Hydrology and Water Resources Symposium, Institution of Engineers Australia, Newcastle: 317-324.
    # Eckhardt, K., 2005. How to construct recursive digital filters for baseflow separation. Hydrological Processes 19, 507-515.
    bfimax = 0.8
    c = (1-k)*bfimax/(1-bfimax)
    a = k/(1+c)
    b = c/(1+c)
    c = 0
    dfo['BoughtonEckhardt'] = digitalFilter(df[['Val']].to_numpy(),a,b,c,1)

    # Jakeman, A.J. and Hornberger G.M., 1993. How much complexity is warranted in a rainfall-runoff model? Water Resources Research 29: 2637-2649.
    a = k
    c = (1-k)*bfimax/(1-bfimax)
    a = a/(1+c)
    b = c/(1+c)
    c = b * -math.exp(-1/k)
    dfo['JakemanHornberger'] = digitalFilter(df[['Val']].to_numpy(),a,b,c,1)

    # Tularam, A.G., Ilahee, M., 2008. Exponential Smoothing Method of Base Flow Separation and its Impact on Continuous Loss Estimates. American Journal of Environmental Sciences 4(2):136-144.
    a = k
    b = 1-a
    c = 0
    dfo['TularamIlahee'] = digitalFilter(df[['Val']].to_numpy(),a,b,c,1)

    ###
    # MOVING WINDOW
    N = math.ceil(Ndays(dakm2))

    # Institute of Hydrology, 1980. Low Flow Studies report. Wallingford, UK.
    # Piggott, A.R., S. Moin, C. Southam, 2005. A revised approach to the UKIH method for the calculation of baseflow. Hydrological Sciences Journal 50(5): 911-920.
    uk = ukih(df, N)
    dfo['sweepingMin'] = uk['sweepingMin']
    dfo['sweepingMax'] = uk['sweepingMax']
    dfo['sweepingMedian'] = uk['sweepingMedian']

    # Sloto, R.A. and M.Y. Crouse, 1996. HYSEP: A Computer Program for Streamflow Hydrograph Separation and Analysis U.S. Geological Survey Water-Resources Investigations Report 96-4040.
    sc = hysep(df, N)
    dfo['fixedInterval'] = sc['FI']
    dfo['slidingInterval'] = sc['SI']
    dfo['localMinimum'] = sc['LM']

    # Rutledge, A.T., 1998. Computer Programs for Describing the Recession of Ground-Water Discharge and for Estimating Mean Ground-Water Recharge and Discharge from Streamflow Records-Update, Water-Resources Investigation Report 98-4148.
    pt = part(df.copy(), N)
    dfo['part1'] = pt.iloc[:, -3]
    dfo['part2'] = pt.iloc[:, -2]
    dfo['part3'] = pt.iloc[:, -1]

    # Clarifica Inc., 2002. Water Budget in Urbanizing Watersheds: Duffins Creek Watershed. Report prepared for the Toronto and Region Conservation Authority.
    dfo['Clarifica'] = clarifica(df)

    nc = len(dfo.columns)
    dfo['min'] = dfo.iloc[:,1:nc].min(axis=1)
    dfo['max'] = dfo.iloc[:,1:nc].max(axis=1)
    dfo['median'] = dfo.iloc[:,1:nc].median(axis=1)

    return dfo.iloc[:, -1] # returning median