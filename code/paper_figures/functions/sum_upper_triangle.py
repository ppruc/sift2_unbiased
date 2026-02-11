import numpy as np

def sum_upper_triangle(df):
    """Sum all values in the upper triangle (including the diagonal), ignoring NaNs."""
    triu = np.triu(df.values, k=0)
    return np.nansum(triu)