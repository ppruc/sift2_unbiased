import pandas as pd 
import numpy as np
import sys
import os

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from update_index import update_index
from normalise_to_fiber_count import normalise_to_fiber_count

def load_streamline_count(data_path, tck_str_abs, normalise=None):
    """
    Load NoS Cross-Sectional connectomes.
    Returns timepoint 1 and timepoint 2 connectome DataFrames.
    """
    tp1 = update_index(pd.read_csv(
        f"{data_path}/simulations/sift2_none/{tck_str_abs}/connectome_tp1.csv",
        header=None))
    
    tp2 = update_index(pd.read_csv(
        f"{data_path}/simulations/sift2_none/{tck_str_abs}/connectome_tp2.csv",
        header=None)) 
    
    if normalise is not None:
        fiber_count_tp1 = normalise
        normalisation_factor_ses1 = normalise_to_fiber_count(tp1,fiber_count_tp1)
        tp1 *= normalisation_factor_ses1
        tp2 *= normalisation_factor_ses1
    
    return tp1, tp2