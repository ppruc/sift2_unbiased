import os
import pandas as pd
import numpy as np
import sys

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from update_index import update_index
from streamline_count import streamline_count
from compute_groundtruth_bundles import compute_groundtruth_bundles
from extract_bundles import extract_bundles
from scale_bundle_errors import scale_bundle_errors
from load_sift2_cross import load_sift2_cross


def extract_absolute_errors(phantom_path,tcks,reg_basis_abs,reg_fn_abs,reg_strengths_abs,scale=False):
    
    errors_true = {}
    errors_false = {}

    base_path = f"{phantom_path}/simulations/sift2_cross/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/"
    
    # Load ground truth and compute difference
    fiber_count_tp1 = streamline_count(f'{phantom_path}/orig/ground_truth/tp1/tracks_gt_tp1.tck')

    gt_tp1 = update_index(pd.read_csv(f"{phantom_path}/orig/ground_truth/tp1/gt_sift2_tp1.csv", header=None))
    gt_tp2 = update_index(pd.read_csv(f"{phantom_path}/orig/ground_truth/tp2/gt_sift2_tp2.csv", header=None))
    gt_tp1[gt_tp1 < 3] = 0 # Filtering two spurious fibres in the original phantom (self assigned to node)
    gt_tp2[gt_tp2 < 3] = 0 # Filtering two spurious fibres in the original phantom (self assigned to node)

    # Determine ground truth bundles by comparing gt_tp1 and gt_tp2
    true_bundles_with_effect, true_bundles_no_effect, false_bundles = compute_groundtruth_bundles(gt_tp1, gt_tp2)

    # Combine all true positive bundles (with and without effect) and calculate mean ground truth
    true_bundles_all = true_bundles_with_effect + true_bundles_no_effect
    gt_true_all = extract_bundles(gt_tp1, true_bundles_all)
    mean_true_all = gt_true_all.replace(0, np.nan).stack().mean()

    for strength in reg_strengths_abs:
            
            path = f"{base_path}/reg_abs_{strength}/"
            print(f"extracting error from {path}")

            # Load the reconstructed connectome; noramlise to fibre count to faciliate comparison with ground truth 
            tp1, _ = load_sift2_cross(phantom_path, tcks, reg_basis_abs, reg_fn_abs, strength, normalise=fiber_count_tp1)
            
            # Compute the absolute difference between reconstructed and ground truth connectome
            error_tp1 = abs(tp1 - gt_tp1)

            # From the error df, extract the bundles of each category
            error_temp_true   = extract_bundles(error_tp1, true_bundles_all)
            error_temp_false  = extract_bundles(error_tp1, false_bundles)

            # For each bundle category, extract the corresponding ground truth from gt_tp1
            gt_true   = extract_bundles(gt_tp1, true_bundles_all)
            gt_false   = extract_bundles(gt_tp1, false_bundles)  

            # Scale each element by the corresponding gt_tp1 value; if zero (false-positives) mean true all is used
            error_temp_true_scaled   = scale_bundle_errors(error_temp_true, gt_true, mean_true_all) * 100
            error_temp_false_scaled            = scale_bundle_errors(error_temp_false, gt_false, mean_true_all) * 100  
            
            # Store the dataframes keyed by the current reg_strength
            if scale:
                errors_true[strength] = error_temp_true_scaled
                errors_false[strength] = error_temp_false_scaled
            else:
                errors_true[strength] = error_temp_true
                errors_false[strength] = error_temp_false

    return (errors_true, errors_false)
