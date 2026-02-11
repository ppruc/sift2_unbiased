import pandas as pd 
import numpy as np
import sys
import os

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from update_index import update_index
from normalise_to_fiber_count import normalise_to_fiber_count


def load_sift2_sym(data_path, tck_str, reg_basis_sym, reg_fn_sym, reg_strength_sym, normalise=None):
    """
    Load SIFT2 Unbiased connectomes.
    Returns timepoint 1 and timepoint 2 connectome DataFrames.
    """
    tp1 = update_index(pd.read_csv(
        f"{data_path}/simulations/sift2_symmetric/{tck_str}/reg_basis_abs_{reg_basis_sym}/reg_fn_abs_{reg_fn_sym}/reg_abs_{reg_strength_sym}/connectome_tp1.csv",
        header=None)) * np.loadtxt(
        f"{data_path}/simulations/sift2_symmetric/{tck_str}/reg_basis_abs_{reg_basis_sym}/reg_fn_abs_{reg_fn_sym}/reg_abs_{reg_strength_sym}/sift2_mu_tp1.txt")
    
    tp2 = update_index(pd.read_csv(
        f"{data_path}/simulations/sift2_symmetric/{tck_str}/reg_basis_abs_{reg_basis_sym}/reg_fn_abs_{reg_fn_sym}/reg_abs_{reg_strength_sym}/connectome_tp2.csv",
        header=None)) * np.loadtxt(
        f"{data_path}/simulations/sift2_symmetric/{tck_str}/reg_basis_abs_{reg_basis_sym}/reg_fn_abs_{reg_fn_sym}/reg_abs_{reg_strength_sym}/sift2_mu_tp2.txt")
    
    if normalise is not None:
        fiber_count_tp1 = normalise
        normalisation_factor_ses1 = normalise_to_fiber_count(tp1,fiber_count_tp1)
        tp1 *= normalisation_factor_ses1
        tp2 *= normalisation_factor_ses1

    return tp1, tp2
