import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command

def stats_connectome(derivatives_dir,ntcks,algorithm="tfnbs",nonstationarity=False):
    
    os.chdir(derivatives_dir)
    
    for group in ("sift2_none", "sift2_cross", "sift2_init", "sift2_differential"):
    
        for contrast in (-1,1):
            
            change_type = "increases" if contrast == 1 else "decreases"
            out_dir = f"stats/{ntcks}/{change_type}{'_nonstationarity' if nonstationarity else ''}/{algorithm}/{group}/"
            os.makedirs(out_dir, exist_ok=True)
                
            run_command(f"connectomestats"
                f" sift2_results/{ntcks}/{group}/fbc_differences/files.txt"
                f" {algorithm}"
                f" template/design_matrix.txt"
                f" template/contrast_matrix_{contrast}.txt"
                f" {out_dir}"
                f" -errors ise"
                f" -force"
                f" {'-nonstationarity' if nonstationarity else ''}"
                )
  