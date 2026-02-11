import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
ss3t_cmd = "/path/to//MRtrix3Tissue/bin/ss3t_csd_beta1" # needs to be installed

def csd(derivatives_dir,sub,ses,ss3t=False):
    
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    run_command(f"mrgrid {ses}/dwi/dwi.mif regrid -vox 1.25 {ses}/dwi/dwi_upsampled.mif -force")

    run_command(f"dwi2mask {ses}/dwi/dwi_upsampled.mif {ses}/dwi/mask_upsampled.nii.gz -force")

    if not ss3t:
        run_command(f"dwi2fod msmt_csd {ses}/dwi/dwi_upsampled.mif ../group_average_response_wm.txt {ses}/dwi/wmfod.mif ../group_average_response_gm.txt {ses}/dwi/gm.mif ../group_average_response_csf.txt {ses}/dwi/csf.mif -mask {ses}/dwi/mask_upsampled.nii.gz -force")
    else:
        run_command(f"{ss3t_cmd} {ses}/dwi/dwi_upsampled.mif ../group_average_response_wm.txt {ses}/dwi/wmfod.mif ../group_average_response_gm.txt {ses}/dwi/gm.mif ../group_average_response_csf.txt {ses}/dwi/csf.mif -mask {ses}/dwi/mask_upsampled.nii.gz -force")

    run_command(f"mtnormalise {ses}/dwi/wmfod.mif {ses}/dwi/wmfod_norm.mif {ses}/dwi/gm.mif {ses}/dwi/gm_norm.mif {ses}/dwi/csf.mif {ses}/dwi/csf_norm.mif -mask {ses}/dwi/mask_upsampled.nii.gz -force")

    
            
