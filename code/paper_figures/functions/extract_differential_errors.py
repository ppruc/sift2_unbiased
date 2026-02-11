import matplotlib.pyplot as plt
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
from load_sift2_diff import load_sift2_diff 


def extract_differential_errors(phantom_path,tcks,reg_basis_abs,reg_fn_abs,reg_strength_abs,reg_fn_diff,reg_basis_diff,reg_strengths_diff,scale=False):
    
    errors_true_effect = {}
    errors_true_no_effect = {}
    errors_false = {}

    base_path = f"{phantom_path}/simulations/sift2_differential/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/"
    
    # Load ground truth and compute difference
    fiber_count_tp1 = streamline_count(f'{phantom_path}/orig/ground_truth/tp1/tracks_gt_tp1.tck')
    gt_tp1 = update_index(pd.read_csv(f"{phantom_path}/orig/ground_truth/tp1/gt_sift2_tp1.csv", header=None))
    gt_tp2 = update_index(pd.read_csv(f"{phantom_path}/orig/ground_truth/tp2/gt_sift2_tp2.csv", header=None))
    gt_tp_diff = (gt_tp2 - gt_tp1).fillna(0)

    # Determine ground truth bundles by comparing gt_tp1 and gt_tp2.
    true_bundles_with_effect, true_bundles_no_effect, false_bundles = compute_groundtruth_bundles(gt_tp1, gt_tp2)

    # Combine all true positive bundles (with and without effect) and calculate mean ground truth.
    true_bundles_all = true_bundles_with_effect + true_bundles_no_effect
    gt_true_all = extract_bundles(gt_tp1, true_bundles_all)
    mean_true_all = gt_true_all.replace(0, np.nan).stack().mean()

    # Filtering two spurious streamlines in the original phantom (self assigned to node)
    gt_tp1[gt_tp1 < 3] = 0
    gt_tp2[gt_tp2 < 3] = 0

    for strength in reg_strengths_diff:
            
            path = f"{base_path}/reg_diff_{strength}/"
            print(f"extracting error from {path}")

            # Load the reconstructed connectomes for TP1 and TP2; noramlise to fibre count to faciliate comparison with ground truth 
            tp1, tp2 = load_sift2_diff(phantom_path, tcks, reg_basis_abs, reg_fn_abs, reg_strength_abs, reg_fn_diff, reg_basis_diff, strength, normalise=fiber_count_tp1)
            tp_diff = tp2 - tp1
            
            # Compute the absolute difference between reconstructed and ground truth differential connectomes
            error_diff = abs(tp_diff - gt_tp_diff)

            # From the error df, extract the bundles of each category
            error_diff_true_no_effect   = extract_bundles(error_diff, true_bundles_no_effect)
            error_diff_true_with_effect = extract_bundles(error_diff, true_bundles_with_effect)
            error_diff_false            = extract_bundles(error_diff, false_bundles)

            # For each bundle category, extract the corresponding ground truth from gt_tp1.
            gt_without = extract_bundles(gt_tp1, true_bundles_no_effect)
            gt_with    = extract_bundles(gt_tp1, true_bundles_with_effect)
            gt_false   = extract_bundles(gt_tp1, false_bundles)  # zero

            # Scale each element by the corresponding gt_tp1 value; if zero (false-positives) mean true all is used
            error_diff_true_no_effect_scaled   = scale_bundle_errors(error_diff_true_no_effect, gt_without, mean_true_all) * 100
            error_diff_true_with_effect_scaled = scale_bundle_errors(error_diff_true_with_effect, gt_with, mean_true_all) * 100
            error_diff_false_scaled            = scale_bundle_errors(error_diff_false, gt_false, mean_true_all) * 100  
            
            # Store the dataframes keyed by the current reg_strength
            if scale:
                errors_true_effect[strength] = error_diff_true_with_effect_scaled
                errors_true_no_effect[strength] = error_diff_true_no_effect_scaled
                errors_false[strength] = error_diff_false_scaled
            else:
                errors_true_effect[strength] = error_diff_true_with_effect
                errors_true_no_effect[strength] = error_diff_true_no_effect
                errors_false[strength] = error_diff_false

    return (errors_true_effect, errors_true_no_effect, errors_false)
