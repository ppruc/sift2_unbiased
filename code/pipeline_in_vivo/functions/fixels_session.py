import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command

def fixels_session(derivatives_dir,sub,ses):

    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)
            
    run_command(f"rm -r {ses}/fixels/")
    run_command(f"mkdir -p {ses}/fixels/fd")
    
    run_command(f"fod2fixel"
        f" -mask {ses}/dwi/mask_upsampled.nii.gz"
        f" -fmls_peak_value 0.06"
        f" {ses}/dwi/wmfod_norm.mif"
        f" {ses}/fixels/fd"
        f" -afd {ses}.mif"
        f" -maxnum 4"
        f" -force"
        )

            
        
        
