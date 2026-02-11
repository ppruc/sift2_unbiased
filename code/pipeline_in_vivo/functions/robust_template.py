import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def robust_template(derivatives_dir,sub,final_template=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions

    os.makedirs(f"ses-average/template/inputs/T1w", exist_ok=True)
    os.makedirs(f"ses-average/template/outputs/", exist_ok=True)
    
    for ses in sessions:
        os.makedirs(f"ses-average/transforms/{ses}", exist_ok=True)
    
        run_command(f"mri_convert {ses}/anat/T1w_Final_brain.nii.gz {ses}/anat/tmp_T1w_Final_brain.nii.gz -c")
    
    run_command(f"mri_robust_template"
        f" --mov {ses1}/anat/tmp_T1w_Final_brain.nii.gz {ses2}/anat/tmp_T1w_Final_brain.nii.gz"
        f" --template ses-average/template/outputs/template_rigid.nii.gz"
        f" --lta ses-average/transforms/{ses1}/sub2temp_rigid.lta ses-average/transforms/{ses2}/sub2temp_rigid.lta"
        f" --average 0"
        f" -satit"
        )
    
    # Convert freesurfer transforms to mrtrix transforms
    for ses in sessions:
        run_command(f"lta_convert --inlta ses-average/transforms/{ses}/sub2temp_rigid.lta --outfsl ses-average/transforms/{ses}/sub2temp_rigid.mat")
        
        run_command(f"transformconvert ses-average/transforms/{ses}/sub2temp_rigid.mat"
            f" {ses}/anat/tmp_T1w_Final_brain.nii.gz"
            f" ses-average/template/outputs/template_rigid.nii.gz"
            f" flirt_import"
            f" ses-average/transforms/{ses}/sub2temp_rigid.txt"
            f" -force"
            )
            
    for ses in sessions:
        run_command(f"rm {ses}/anat/tmp_T1w_Final_brain.nii.gz")
        
    if final_template:
        run_command(f"mrconvert ses-average/template/outputs/template_rigid.nii.gz ses-average/template/t1w_template.nii.gz -force")
        run_command(f"mrthreshold ses-average/template/t1w_template.nii.gz ses-average/template/t1w_template_mask.nii.gz -abs 10 -force")
        run_command(f"rm ses-average/template/tmp*")
        run_command(f"rm ses-average/template/mri_nu*")



    
