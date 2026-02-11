import pandas as pd

def update_index(input_df):
    """Reset DataFrame index and columns so that indexing starts at 1."""
    df = input_df.copy()
    df.index = range(1, len(df) + 1)
    df.columns = range(1, len(df.columns) + 1)
    return df