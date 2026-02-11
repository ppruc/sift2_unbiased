import pandas as pd 
import numpy as np

def scale_bundle_errors(error_df, gt_df, mean_true):
    """
    Scale the error DataFrame on an elementwise basis.
    For each element, if the corresponding ground truth (gt_df) is greater than 0,
    error_scaled = error / (ground truth value); otherwise, error_scaled = error / mean_true.
    """
    denom = np.where(gt_df.values > 0, gt_df.values, mean_true)
    scaled_values = error_df.values / denom
    return pd.DataFrame(scaled_values, index=error_df.index, columns=error_df.columns)
