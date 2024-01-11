import math

def saturationVapourPressure(tC): #[Pa]
	# August-Roche-Magnus approximation (from pg.38 of Lu, N. and J.W. Godt, 2013. Hillslope Hydrology and Stability. Cambridge University Press. 437pp.)
	# for -30°C =< T =< 50°C
	return 610.49 * math.exp(17.625*tC/(tC+243.04)) # [Pa=N/m²] R²=1


def vapourPressureDeficit(tC, rh):
    # if rh > 1. or rh < 0.: print("ERROR vapourPressureDeficit: relative humidity out of range [0,1]: {}".format(rh))
    return (1. - rh) * saturationVapourPressure(tC)