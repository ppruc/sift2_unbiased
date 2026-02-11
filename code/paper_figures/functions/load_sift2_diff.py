import pandas as pd 
import numpy as np
import sys
import os

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from update_index import update_index
from normalise_to_fiber_count import normalise_to_fiber_count


def load_sift2_diff(data_path, tck_str, reg_basis_abs, reg_fn_abs, reg_strength_abs, reg_fn_diff, reg_basis_diff, reg_strength_diff, normalise=None):
    """
    Loads SIFT2 Differential connectomes.
    Returns the TP1 connectome and TP2 connectome.
    """
    tp_av = update_index(pd.read_csv(
        f"{data_path}/simulations/sift2_differential/{tck_str}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/"
        f"reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/reg_diff_{reg_strength_diff}/connectome.csv",
        header=None)) * np.loadtxt(
        f"{data_path}/simulations/sift2_differential/{tck_str}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/"
        f"reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/reg_diff_{reg_strength_diff}/sift2_mu.txt")
    
    tp_diff = update_index(pd.read_csv(
        f"{data_path}/simulations/sift2_differential/{tck_str}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/"
        f"reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/reg_diff_{reg_strength_diff}/connectome_diff_half.csv",
        header=None)) * 2 * np.loadtxt(
        f"{data_path}/simulations/sift2_differential/{tck_str}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/"
        f"reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/reg_diff_{reg_strength_diff}/sift2_mu.txt")
    
    tp1 = tp_av - (tp_diff / 2)
    tp2 = tp_av + (tp_diff / 2)

    if normalise is not None:
        fiber_count_tp1 = normalise
        normalisation_factor_ses1 = normalise_to_fiber_count(tp1,fiber_count_tp1)
        tp1 *= normalisation_factor_ses1
        tp2 *= normalisation_factor_ses1

    return tp1, tp2