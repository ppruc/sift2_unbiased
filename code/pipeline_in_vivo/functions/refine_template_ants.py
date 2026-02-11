import os
import sys
import shutil

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions
from convert_warp_ants2mrtrix import convert_warp_ants2mrtrix

def refine_template_ants(derivatives_dir,sub,cores=30,use_bet=False,fs_conform_inputs=False,final_template=False):

    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    
    #shutil.rmtree(f"ses-average/template/inputs/")
    #shutil.rmtree(f"ses-average/template/outputs/")
        
    os.makedirs(f"ses-average/template/inputs/T1w/", exist_ok=True)
    os.makedirs(f"ses-average/template/outputs/", exist_ok=True)

    for ses in sessions:
    
        # Transform the T1w images to template space
        run_command(f"mrtransform"
                    f" {ses}/anat/T1w_Final{'_brain' if use_bet else ''}.nii.gz"
                    f" ses-average/template/inputs/T1w/{ses}.nii.gz"
                    f" -linear ses-average/transforms/{ses}/sub2temp_rigid.txt"
                    f" -force"
                    )
                    
        if fs_conform_inputs:
            print("conforming inputs")
            run_command(f"mri_convert ses-average/template/inputs/T1w/{ses}.nii.gz ses-average/template/inputs/T1w/{ses}.nii.gz -c")

    # create non-linearily refined template with ANTS
    run_command(f"antsMultivariateTemplateConstruction2.sh"
                f" -d 3"
                f" -l 0"
                f" -a 1"
                f" -n 1"
                f" -c 2"
                f" -j {cores}"
                f" -o ses-average/template/outputs/ants_refined_"
                f" ses-average/template/inputs/T1w/{ses1}.nii.gz ses-average/template/inputs/T1w/{ses2}.nii.gz"
                )
    
    # Intensity normalize ANTS template
    run_command(f"mri_nu_correct.mni --i ses-average/template/outputs/ants_refined_template0.nii.gz --o #ses-average/template/outputs/tmp_ants_refined_template0_N3.nii.gz --n 2")
    run_command(f"mri_normalize -g 1 -mprage ses-average/template/outputs/tmp_ants_refined_template0_N3.nii.gz #ses-average/template/outputs/template_nonlinear.nii.gz")

    for ses in sessions:
    
        # Convert ants warps to mrtrix warps
        cond1 = os.path.exists(f"ses-average/template/outputs/ants_refined_{ses}{'0' if ses == ses1 else '1'}1Warp.nii.gz")
        cond2 = os.path.exists(f"ses-average/template/outputs/ants_refined_input000{'0' if ses == ses1 else '1'}-{ses}-1Warp.nii.gz")
        
        if cond2 and not cond1:
            print("cond2 True")
            convert_warp_ants2mrtrix("ses-average/template/outputs/ants_refined_template0.nii.gz",f"ses-average/template/inputs/T1w/{ses}.nii.gz",f"ses-average/template/outputs/ants_refined_input000{'0' if ses == ses1 else '1'}-{ses}-",f"ses-average/transforms/{ses}/temp_rigid2temp_ants_deformation.mif")
        
        elif cond1 and not cond2:
            print("cond1 True")
            convert_warp_ants2mrtrix("ses-average/template/outputs/ants_refined_template0.nii.gz",f"ses-average/template/inputs/T1w/{ses}.nii.gz",f"ses-average/template/outputs/ants_refined_{ses}{'0' if ses == ses1 else '1'}",f"ses-average/transforms/{ses}/temp_rigid2temp_ants_deformation.mif")
        
        else:
            print(f"both conditions TRUE for {sub}")
    
        # Generate subject to ants template transforms
        # Compose transforms
        run_command(f"transformcompose"
                f" ses-average/transforms/{ses}/sub2temp_rigid.txt"
                f" ses-average/transforms/{ses}/temp_rigid2temp_ants_deformation.mif"
                f" ses-average/transforms/{ses}/sub2temp_ants_deformation.mif"
                f" -force"
                )
        
        # Invert transforms
        run_command(f"warpinvert ses-average/transforms/{ses}/sub2temp_ants_deformation.mif ses-average/transforms/{ses}/sub2temp_ants_deformation_inv.mif -force")
    
        # Transform & resample preop + postop T1w image
        run_command(f"mrtransform {ses}/anat/T1w_Final.nii.gz ses-average/template/outputs/T1w_Final_{ses}_resampled.nii.gz -warp ses-average/transforms/{ses}/sub2temp_ants_deformation.mif -force")
        
        run_command(f"mri_synthstrip -i ses-average/template/outputs/T1w_Final_{ses}_resampled.nii.gz -o ses-average/template/outputs/T1w_Final_{ses}_resampled_brain.nii.gz -m ses-average/template/outputs/T1w_Final_{ses}_resampled_mask.nii.gz")
        
    run_command(f"mrmath ses-average/template/outputs/T1w_Final_{ses1}_resampled.nii.gz ses-average/template/outputs/T1w_Final_{ses2}_resampled.nii.gz mean ses-average/template/outputs/template_nonlinear.nii.gz -force")
    
    if final_template:
        run_command(f"mri_synthstrip -i ses-average/template/outputs/template_nonlinear.nii.gz -o ses-average/template/outputs/template_nonlinear_brain.nii.gz -m ses-average/template/outputs/template_nonlinear_mask.nii.gz")
        run_command(f"mrconvert ses-average/template/outputs/template_nonlinear_brain.nii.gz ses-average/template/t1w_template.nii.gz -force")
        run_command(f"mrconvert ses-average/template/outputs/template_nonlinear_mask.nii.gz ses-average/template/t1w_template_mask.nii.gz -force")

    # Clean up
    for ses in sessions:
        run_command(f"rm {ses}/anat/tmp*")
    run_command(f"rm ses-average/template/outputs/tmp_*")
    run_command(f"rm ses-average/template/outputs/mri_nu*")

 
