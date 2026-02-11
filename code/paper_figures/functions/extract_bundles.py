import pandas as pd 
import numpy as np

def extract_bundles(df, bundles):
    """
    Extract a subset of a connectome matrix based on the specified bundle indices.
    Only the entries corresponding to the provided (i, j) pairs are retained.
    """
    df_extracted = pd.DataFrame(np.nan, index=df.index, columns=df.columns)
    for i, j in bundles:
        df_extracted.loc[i, j] = df.loc[i, j]
    return df_extracted