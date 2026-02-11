import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def impute_template(derivatives_dir, sub):
    
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, _ = sessions
        
    # Impute preoperative values of resection zone into ants refined template
    run_command(f"maskfilter ses-average/surg_defect/surg_defect_unsegmented.nii.gz dilate ses-average/template/outputs/tmp_surg_defect_logic_dilate.nii.gz -npass 4 -force")
    run_command(f"mrfilter ses-average/template/outputs/tmp_surg_defect_logic_dilate.nii.gz smooth ses-average/template/outputs/tmp_surg_defect_logic_smooth.nii.gz -fwhm 6 -force")
    run_command(f"mrcalc 1 ses-average/template/outputs/tmp_surg_defect_logic_smooth.nii.gz -sub ses-average/template/outputs/tmp_surg_defect_logic_smooth_inverted.nii.gz -force")
    run_command(f"mrcalc ses-average/template/outputs/tmp_surg_defect_logic_smooth.nii.gz ses-average/template/outputs/T1w_Final_{ses1}_resampled.nii.gz -mult ses-average/template/outputs/tmp_resection_imputed.nii.gz -force")
    run_command(f"mrcalc ses-average/template/outputs/tmp_surg_defect_logic_smooth_inverted.nii.gz ses-average/template/outputs/template_nonlinear.nii.gz -mult ses-average/template/outputs/tmp_norm_template_resected.nii.gz -force")
    run_command(f"mrcalc ses-average/template/outputs/tmp_norm_template_resected.nii.gz ses-average/template/outputs/tmp_resection_imputed.nii.gz -add ses-average/template/outputs/norm_template_imputed.nii.gz -force")
    run_command(f"mri_synthstrip -i ses-average/template/outputs/norm_template_imputed.nii.gz -o ses-average/template/outputs/norm_template_imputed_brain.nii.gz -m ses-average/template/outputs/norm_template_imputed_mask.nii.gz")
    run_command(f"mrconvert ses-average/template/outputs/norm_template_imputed_brain.nii.gz ses-average/template/t1w_template.nii.gz -force")

    
    # Remove unneeded files
    run_command(f"rm ses-average/template/outputs/tmp*")
