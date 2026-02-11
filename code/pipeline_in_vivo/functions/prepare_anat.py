import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command

def prepare_anat(derivatives_dir,sub,ses,skip_coreg=False):
    
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)
    
    run_command(f"mri_nu_correct.mni --i {ses}/anat/T1w.nii.gz --o {ses}/anat/tmp_T1w_N3.nii.gz --n 2")
    run_command(f"mri_normalize -g 1 -mprage {ses}/anat/tmp_T1w_N3.nii.gz {ses}/anat/tmp_T1w_norm.nii.gz")
    
    if not skip_coreg:

        run_command(f"dwi2tensor {ses}/dwi/dwi_upsampled.mif {ses}/dwi/tensor.mif -mask {ses}/dwi/mask_upsampled.nii.gz -force")
                
        run_command(f"tensor2metric {ses}/dwi/tensor.mif -fa {ses}/dwi/FA.nii.gz -force")

        run_command(f"mri_synthstrip -i {ses}/anat/tmp_T1w_norm.nii.gz -o {ses}/anat/T1w_brain.nii.gz -m {ses}/anat/mask.nii.gz")

        run_command(f"antsRegistrationSyN.sh"
                            f" -d 3"
                            f" -x {ses}/dwi/mask_upsampled.nii.gz,{ses}/anat/mask.nii.gz"
                            f" -m {ses}/anat/T1w_brain.nii.gz"
                            f" -f {ses}/dwi/FA.nii.gz"
                            f" -o {ses}/anat/tmp_anat2dwi_"
                            f" -t r"
                            )
                            
        run_command(f"antsApplyTransforms"
                            f" -d 3"
                            f" -e 0"
                            f" -i {ses}/anat/tmp_T1w_norm.nii.gz"
                            f" -o {ses}/anat/T1w_Final.nii.gz"
                            f" -r {ses}/anat/T1w_brain.nii.gz"
                            f" -t {ses}/anat/tmp_anat2dwi_0GenericAffine.mat"
                            )
        
        run_command(f"rm {ses}/anat/T1w_brain.nii.gz")
        
    else:
        
        run_command(f"cp {ses}/anat/tmp_T1w_norm.nii.gz {ses}/anat/T1w_Final.nii.gz")
        
    run_command(f"mri_synthstrip -i {ses}/anat/T1w_Final.nii.gz -o {ses}/anat/T1w_Final_brain.nii.gz -m {ses}/anat/T1w_Final_mask.nii.gz")
    
    run_command(f"rm {ses}/anat/tmp*")
        

    
                    
        
        

