import pandas as pd 
import numpy as np

def compute_groundtruth_bundles(matrix1, matrix2):
    """
    Determine ground truth bundles by comparing two matrices:
      - 'with effect': the entry changes between timepoints.
      - 'without effect': the entry is nonzero and unchanged.
      - 'false bundle': the entry is zero in both.
    Indices are shifted so that numbering starts at 1.
    """
    if matrix1.shape != matrix2.shape:
        raise ValueError("Both matrices must have the same shape.")
    
    true_with, true_no, false_bundles = [], [], []
    n_rows, n_cols = matrix1.shape
    for i in range(n_rows):
        for j in range(n_cols):
            val1 = matrix1.iloc[i, j]
            val2 = matrix2.iloc[i, j]
            if val1 != val2:
                true_with.append((i+1, j+1))
            elif val1 != 0:
                true_no.append((i+1, j+1))
            else:
                false_bundles.append((i+1, j+1))
    return true_with, true_no, false_bundles