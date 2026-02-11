import sys
import os

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def make_derivatives(bids_dir):

    os.chdir(bids_dir)
    
    derivatives_dir = os.path.join(bids_dir, "derivatives")
    os.makedirs(derivatives_dir, exist_ok=True)
    
    subs = [item for item in os.listdir(bids_dir) if item.startswith("sub-")]

    for sub in subs:
        
        for ses in get_sessions(bids_dir, sub):
        
            if len(os.listdir(os.path.join(bids_dir,sub))) > 1:

                os.makedirs(f"{derivatives_dir}/{sub}/{ses}/dwi/",exist_ok=True)
                os.makedirs(f"{derivatives_dir}/{sub}/{ses}/anat/",exist_ok=True)

                run_command(f"mrconvert"
                    f" {bids_dir}/{sub}/{ses}/dwi/dwmri.nii.gz"
                    f" {derivatives_dir}/{sub}/{ses}/dwi/dwi.mif"
                    f" -fslgrad {bids_dir}/{sub}/{ses}/dwi/dwmri.bvec"
                    f" {bids_dir}/{sub}/{ses}/dwi/dwmri.bval -force"
                )
                
                run_command(f"mrconvert {bids_dir}/{sub}/{ses}/anat/{sub}_{ses}_T1w.nii.gz {derivatives_dir}/{sub}/{ses}/anat/T1w.nii.gz -force")
            
            else:
                print(f"Skipping {sub} as only single session available")
                

