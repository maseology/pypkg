
import numpy as np
from scipy import interpolate

def infill(arr: np.ndarray) -> np.ndarray:
    """
    Fills in holes to make a contiguous surface.
    """
    active = arr>-999.
    nonactive = ~active

    if not nonactive.any(): return arr.copy()
    nr, nc = arr.shape
    y_grid, x_grid = np.mgrid[0:nr, 0:nc]

    points_known = np.column_stack((x_grid[active], y_grid[active]))
    values_known = arr[active]
    points_hole = np.column_stack((x_grid[nonactive], y_grid[nonactive]))
    interpolated_vals = interpolate.griddata(points_known, values_known, points_hole, method="linear",fill_value=-9999.)    

    filled = arr.astype(float).copy()
    filled[nonactive] = interpolated_vals
    
    return filled


def coarsen(a, cf, nrows, ncols): return a.reshape(nrows//cf, cf, ncols//cf, cf)

def coarseMin(a, cf, nrows, ncols): # downscale grid by factor f, taking the minimum of the fxf aggregated cell
    if cf<=1: return a
    coarse = coarsen(a, cf, nrows, ncols)
    msk = (coarse > -999.).all(axis=(1, 3)) # only downscaling where all fxf cells have values, otherwise nodata
    dmin = coarse.min(axis=(1, 3))
    return np.where(msk, dmin, -9999.)

def coarseMax(a, cf, nrows, ncols): # downscale grid by factor f, taking the minimum of the fxf aggregated cell
    if cf<=1: return a
    coarse = coarsen(a, cf, nrows, ncols)
    msk = (coarse > -999.).all(axis=(1, 3)) # only downscaling where all fxf cells have values, otherwise nodata
    dmax = coarse.min(axis=(1, 3))
    return np.where(msk, dmax, -9999.)

def coarseMean(a, cf, nrows, ncols, noNan=True): # downscale grid by factor f, taking the mean of the fxf aggregated cell
    if cf<=1: return a
    coarse = coarsen(a, cf, nrows, ncols)
    if noNan:
        msk = (coarse > -999.).all(axis=(1, 3)) # only downscaling where all fxf cells have value, otherwise nodata
        dmean = coarse.mean(axis=(1, 3))
        return np.where(msk, dmean, -9999.)
    else:
        msk = coarse>-999.
        masked_coarse = np.where(msk, coarse, 0) # zero-out nodata cells
        sum_coarse = masked_coarse.sum(axis=(1, 3))
        count_coarse = msk.sum(axis=(1, 3))
        with np.errstate(divide='ignore', invalid='ignore'):
            return np.where(count_coarse==0, -9999., sum_coarse / count_coarse)


def flagSurrounded(arr: np.ndarray) -> np.ndarray:
    """
    Returns mask when the four cardinal neighbours of the cell are all > -999; arr 
    Border cells are always False because they lack a full set of neighbours.
    """
    # Extract interior slices
    up    = arr[:-2, 1:-1]   # neighbour above each interior cell
    down  = arr[2:,  1:-1]   # neighbour below
    left  = arr[1:-1, :-2]   # neighbour left
    right = arr[1:-1, 2:]    # neighbour right

    interior_mask = (up > -999.) & (down > -999.) & (left > -999.) & (right > -999.)
    pad_mask = np.pad(interior_mask,
                      pad_width=((1, 1), (1, 1)),
                      mode='constant',
                      constant_values=False)
    return pad_mask

    # A = np.array([[0, 2, 3, 0],
    #               [5,10,-1, 4],
    #               [6, 7, 8, 9],
    #               [0, 1, 2, 0]])

    # mask = flagSurrounded(A)
    # print(mask.astype(int))   # cast to int for pretty printing