import numpy as np
import pandas as pd

def prepare_connectomes(connectome_files, subset_idx=None, start_idx_1=True, log_transform=False, multiply=None):

    connectome_files.sort()

    connectomes_dict = {}

    for i in range(0, len(connectome_files)):
        connectome_file = connectome_files[i]
        connectome_label = connectome_file.split("/")[-1].split("_")[0]
        connectome = pd.read_csv(connectome_file,header=None)

        if multiply != None:
                connectome *= multiply

        if log_transform:
                connectome = np.log1p(connectome)  # log1p to avoid log(0) issues

        if start_idx_1:
                connectome.index = range(1, len(connectome) + 1)
                connectome.columns = range(1, len(connectome.columns) + 1)

        if subset_idx != None:
                start_idx, stop_idx = subset_idx
                connectome = connectome.loc[start_idx:stop_idx, start_idx:stop_idx]
            
        connectomes_dict[connectome_label] = connectome
            
    return connectomes_dict 