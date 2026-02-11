import os
import sys
import shutil

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions
from mask_resample import mask_resample

def wmfod_template(derivatives_dir,sub,reg_type,surgical=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")

    # Create output dirs
    os.makedirs(os.path.join(path, "ses-average", "wmfod_template"), exist_ok=True)
    
    run_command(f"mrgrid ses-average/template/t1w_template.nii.gz regrid ses-average/wmfod_template/tmp_template_grid_vox1.25.nii.gz -vox 1.25 -force")

    for ses in sessions:
        
        if reg_type != 'rigid':
        
            # Regrid warp to vox 1.25 mm3
            run_command(f"mrgrid ses-average/transforms/{ses}/sub2temp_ants_deformation.mif"
                f" regrid"
                f" ses-average/transforms/{ses}/sub2temp_wmfod_deformation.mif"
                f" -template ses-average/wmfod_template/tmp_template_grid_vox1.25.nii.gz"
                f" -force"
                )
        
            # Warp WM odfs from subject space to template (+ reorient + modulate + resample)
            run_command(f"mrtransform"
                f" {ses}/dwi/wmfod_norm.mif"
                f" ses-average/wmfod_template/wmfod_{ses}_resampled.mif"
                f" -warp ses-average/transforms/{ses}/sub2temp_wmfod_deformation.mif"
                f" -reorient yes"
                f" -modulate fod"
                f" -force"
                )
            
            run_command(f"mrtransform"
                f" {ses}/dwi/mask_upsampled.nii.gz"
                f" ses-average/wmfod_template/tmp_mask_{ses}_resampled.mif"
                f" -warp ses-average/transforms/{ses}/sub2temp_wmfod_deformation.mif"
                f" -force"
                )
                
        else:
            # Warp WM odfs from subject space to template (+ reorient + modulate + resample)
            run_command(f"mrtransform"
                f" {ses}/dwi/wmfod_norm.mif"
                f" ses-average/wmfod_template/wmfod_{ses}_resampled.mif"
                f" -linear ses-average/transforms/{ses}/sub2temp_rigid.txt"
                f" -template ses-average/wmfod_template/wmfod_template.mif"
                f" -reorient yes"
                f" -force"
                )
        
            run_command(f"mrtransform"
                f" {ses}/dwi/mask_upsampled.nii.gz"
                f" ses-average/wmfod_template/tmp_mask_{ses}_resampled.mif"
                f" -linear ses-average/transforms/{ses}/sub2temp_rigid.txt"
                f" -template ses-average/wmfod_template/wmfod_template.mif"
                f" -force"
                )
                
        run_command(f"mrthreshold"
            f" ses-average/wmfod_template/tmp_mask_{ses}_resampled.mif"
            f" ses-average/wmfod_template/mask_{ses}_resampled.mif"
            f" -abs 0.5"
            f" -force"
            )
           
    # Calculate the average WM odf template
    run_command(f"mrmath"
            f" ses-average/wmfod_template/wmfod_{ses1}_resampled.mif"
            f" ses-average/wmfod_template/wmfod_{ses2}_resampled.mif"
            f" mean"
            f" ses-average/wmfod_template/{'tmp_' if surgical else ''}wmfod_template.mif"
            f" -keep_unary_axes"
            f" -force"
            )
            
    if surgical:
        mask_resample(f"ses-average/surg_defect/surg_defect_unsegmented.nii.gz", f"ses-average/wmfod_template/tmp_template_grid_vox1.25.nii.gz", "ses-average/surg_defect/surg_defect_unsegmented_vox1.25.nii.gz")
            
        run_command(f"mrcalc"
                    f" 1"
                    f" ses-average/surg_defect/surg_defect_unsegmented_vox1.25.nii.gz"
                    f" -sub ses-average/surg_defect/surg_defect_unsegmented_inv_vox1.25.nii.gz"
                    f" -force"
                    )
                
        run_command(f"mrcalc"
                    f" ses-average/wmfod_template/mask_{ses2}_resampled.mif"
                    f" ses-average/surg_defect/surg_defect_unsegmented_inv_vox1.25.nii.gz"
                    f" -mult ses-average/wmfod_template/mask_{ses2}_resampled_corr.mif"
                    f" -force"
                    )
                    
        # Impute preoperative values of resection zone into ants refined template
        run_command(f"maskfilter ses-average/surg_defect/surg_defect_unsegmented_vox1.25.nii.gz dilate ses-average/wmfod_template/tmp_surg_defect_logic_dilate.mif -npass 4 -force")
        
        run_command(f"mrfilter ses-average/wmfod_template/tmp_surg_defect_logic_dilate.mif smooth ses-average/wmfod_template/tmp_surg_defect_logic_smooth.mif -fwhm 6 -force")
        
        run_command(f"mrcalc 1 ses-average/wmfod_template/tmp_surg_defect_logic_smooth.mif -sub ses-average/wmfod_template/tmp_surg_defect_logic_smooth_inverted.mif -force")
        
        run_command(f"mrcalc ses-average/wmfod_template/tmp_surg_defect_logic_smooth.mif ses-average/wmfod_template/wmfod_{ses1}_resampled.mif -mult ses-average/wmfod_template/tmp_resection_imputed.mif -force")
        
        run_command(f"mrcalc ses-average/wmfod_template/tmp_surg_defect_logic_smooth_inverted.mif ses-average/wmfod_template/tmp_wmfod_template.mif -mult ses-average/wmfod_template/tmp_wmfod_template_resected.mif -force")
        
        run_command(f"mrcalc ses-average/wmfod_template/tmp_wmfod_template_resected.mif ses-average/wmfod_template/tmp_resection_imputed.mif -add ses-average/wmfod_template/wmfod_template.mif -force")

        
    # Calculate intersection mask
    run_command(f"mrmath"
        f" ses-average/wmfod_template/mask_{ses1}_resampled.mif"
        f" ses-average/wmfod_template/mask_{ses2}_resampled.mif"
        f" min"
        f" ses-average/wmfod_template/wmfod_template_mask.mif"
        f" -force"
        )
            
    # Delete tmps
    try:
        run_command("rm ses-average/wmfod_template/tmp*")
    except:
        pass
        
    
