import pandas as pd 
import numpy as np
import sys
import os

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from update_index import update_index
from normalise_to_fiber_count import normalise_to_fiber_count

def load_sift2_temp(data_path, tck_str, reg_basis_abs, reg_fn_abs, reg_strength_abs, normalise=None):
    """
    Load unbiased template connectome.
    Returns the tp av connectome.
    """
    tp_av = update_index(pd.read_csv(
        f"{data_path}/simulations/sift2_template/{tck_str}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/connectome.csv",
        header=None)) * np.loadtxt(
        f"{data_path}/simulations/sift2_template/{tck_str}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/sift2_mu.txt")

    if normalise is not None:
        fiber_count_tpav = normalise
        normalisation_factor = normalise_to_fiber_count(tp_av,fiber_count_tpav)
        tp_av *= normalisation_factor

    return tp_av