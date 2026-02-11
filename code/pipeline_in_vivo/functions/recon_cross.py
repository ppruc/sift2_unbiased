import os
import sys
import shutil

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command

def recon_cross(derivatives_dir,sub,ses,remove_old_run=False,parallel=False,n_threads=1):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    recon_out_path = os.path.join(path,ses,"anat", "recon")

    # Remove old run in case of re-run
    if remove_old_run and os.path.exists(recon_out_path):
            run_command(f"rm -r {recon_out_path}")
            

    run_command(f"recon-all -i {path}/{ses}/anat/T1w_Final.nii.gz -s recon -all -sd {path}/{ses}/anat/ -qcache -threads {n_threads} {'-parallel' if parallel else ''}")
