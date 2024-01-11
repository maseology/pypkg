# import math
from pyDrology import properties as p

# PenmanWind mass density flux mm/s ~kg/m²/s
# Penman (1948) based solely on the wind function
# see Novak 182
def PenmanWind(t, rh, u, a, b):
    if t < -30 or t > 50: print(" Warning PenmanWind: temperature out of range: "+str(t))
    if rh < 0 or rh > 1: print(" Warning PenmanWind: relative humidity out of range: "+str(rh))
    if u < 0 or u > 100: print(" Warning PenmanWind: unexpected wind speed: "+str(u))
    de = p.vapourPressureDeficit(t, rh) # [Pa]
    # return a * de * math.pow(u, b) * 7.46e-6    # [kg/m²/s]
    return  de * (a + b*u) * 7.46e-6    # [kg/m²/s]