import os
import sys
import shutil
from glob import glob
import pandas as pd
import nibabel as nib

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

cmd_tcksift2 = "/home/ppruckner/github/MRtrix3_sift2diff/bin/tcksift2"
cmd_5ttregrid = "/home/ppruckner/github/mrtrix3_5ttregrid/bin/5ttregrid"

def atlas_template(derivatives_dir,dependencies_dir,sub,surgical=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)
    
    os.makedirs(os.path.join(path, "ses-average", "atlases"), exist_ok=True)
    
    if not surgical:
        
        # generate atlas from standard aparc+aseg
        run_command(f"labelconvert"
                        f" ses-average/fs_longitudinal/recon_template/mri/aparc+aseg.mgz"
                        f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                        f" {dependencies_dir}/mrtrix3/labelconvert/fs_default.txt"
                        f" ses-average/atlases/Desikan-Killiany.nii.gz"
                        f" -force"
                        )
    
    else:
    
        # Create ipsi_contra atlas file
        database = pd.read_excel(f"{derivatives_dir}/../morgan_database.xlsx", index_col="sub")
    
        # Invert the surg defect
        run_command(f"mrcalc 1"
            f" ses-average/fs_longitudinal/surg_defect_final_dil_ses-average.nii.gz"
            f" -sub"
            f" ses-average/fs_longitudinal/surg_defect_final_dil_ses-average_inv.nii.gz"
            f" -force"
            )
        
        # Modify aseg file to exclude voxels
        run_command(f"mrcalc"
            f" ses-average/fs_longitudinal/recon_template/mri/aseg.mgz"
            f" ses-average/fs_longitudinal/surg_defect_final_dil_ses-average_inv.nii.gz"
            f" -mult"
            f" ses-average/fs_longitudinal/recon_template/mri/aseg.nonresected.mgz"
            f" -force"
            )
            
        # Modify aseg file to include voxels
        run_command(f"mrcalc"
            f" ses-average/fs_longitudinal/recon_template/mri/aseg.mgz"
            f" ses-average/fs_longitudinal/surg_defect_final_dil_ses-average.nii.gz"
            f" -mult"
            f" ses-average/fs_longitudinal/recon_template/mri/aseg.resected.mgz"
            f" -force"
            )
        
        # Generate corrected aparc+aseg for nonresected.annot and nonresected aseg files
        run_command(f"mri_surf2volseg"
            " --o ses-average/fs_longitudinal/recon_template/mri/aparc+aseg.nonresected.mgz"
            " --label-cortex"
            " --i ses-average/fs_longitudinal/recon_template/mri/aseg.nonresected.mgz"
            " --threads 96"
            " --lh-annot ses-average/fs_longitudinal/recon_template/label/lh.aparc.nonresected.annot 1000"
            " --lh-cortex-mask ses-average/fs_longitudinal/recon_template/label/lh.cortex.label"
            " --lh-white ses-average/fs_longitudinal/recon_template/surf/lh.white"
            " --lh-pial ses-average/fs_longitudinal/recon_template/surf/lh.pial"
            " --rh-annot ses-average/fs_longitudinal/recon_template/label/rh.aparc.nonresected.annot 2000"
            " --rh-cortex-mask ses-average/fs_longitudinal/recon_template/label/rh.cortex.label"
            " --rh-white ses-average/fs_longitudinal/recon_template/surf/rh.white"
            " --rh-pial ses-average/fs_longitudinal/recon_template/surf/rh.pial"
            )
            
        # Generate corrected aparc+aseg for resected.annot and resected aseg files
        run_command(f"mri_surf2volseg"
            f" --o ses-average/fs_longitudinal/recon_template/mri/aparc+aseg.resected.mgz"
            f" --label-cortex"
            f" --i ses-average/fs_longitudinal/recon_template/mri/aseg.resected.mgz"
            f" --threads 96"
            f" --lh-annot ses-average/fs_longitudinal/recon_template/label/lh.aparc.resected.annot 1000"
            f" --lh-cortex-mask ses-average/fs_longitudinal/recon_template/label/lh.cortex.label"
            f" --lh-white ses-average/fs_longitudinal/recon_template/surf/lh.white"
            f" --lh-pial ses-average/fs_longitudinal/recon_template/surf/lh.pial"
            f" --rh-annot ses-average/fs_longitudinal/recon_template/label/rh.aparc.resected.annot 2000"
            f" --rh-cortex-mask ses-average/fs_longitudinal/recon_template/label/rh.cortex.label"
            f" --rh-white ses-average/fs_longitudinal/recon_template/surf/rh.white"
            f" --rh-pial ses-average/fs_longitudinal/recon_template/surf/rh.pial"
            )
        
        # Create a label file for the surg defect with unique identifier (86)
        run_command(f"labelconvert"
            f" ses-average/fs_longitudinal/recon_template/mri/aparc+aseg.resected.mgz"
            f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
            f" {dependencies_dir}/mrtrix3/labelconvert/fs_default.txt"
            f" ses-average/atlases/tmp_Desikan-Killiany_resected.nii.gz"
            f" -force"
            )
        
        run_command(f"mrthreshold"
            f" ses-average/atlases/tmp_Desikan-Killiany_resected.nii.gz"
            f" ses-average/atlases/tmp_Desikan-Killiany_resected_thr.nii.gz"
            f" -abs 0.01"
            f" -force"
            )
        
        run_command(f"mrcalc"
            f" ses-average/atlases/tmp_Desikan-Killiany_resected_thr.nii.gz"
            f" 1"
            f" 86"
            f" -replace"
            f" ses-average/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
            f" -force"
            )
        
        # Create output directory
        for side_type in ("left_right", "ipsi_contra"):
            os.makedirs(os.path.join(path, "ses-average", "atlases", side_type), exist_ok=True)
            
            if side_type == "left_right":
            
                # Create atlas file
                for lut_suffix in [("fs_default","left_right"),("fs_default_lh","left"),("fs_default_rh","right")]:
                    lut, suffix = lut_suffix
                    
                    # generate atlas from nonresected aparc+aseg
                    run_command(f"labelconvert"
                        f" ses-average/fs_longitudinal/recon_template/mri/aparc+aseg.nonresected.mgz"
                        f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                        f" {dependencies_dir}/mrtrix3/labelconvert/{lut}.txt"
                        f" ses-average/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                        f" -force"
                        )
                        
                    # add surg_defect as label
                    run_command(f"mrcalc"
                            f" ses-average/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                            f" ses-average/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
                            f" -add"
                            f" ses-average/atlases/{side_type}/Desikan-Killiany_{suffix}.nii.gz"
                            f" -force"
                            )
          
            else:
                # If left-sided TLE, relabel left to ipsi and right to contra
                if database.loc[sub,"side"] == "L":
                    for lut_suffix in [("fs_default_lh2ipsi_rh2contra","ipsi_contra"),("fs_default_lh2ipsi","ipsi"),("fs_default_rh2contra","contra")]:
                        lut, suffix = lut_suffix
                        # generate atlas from nonresected aparc+aseg
                        run_command(f"labelconvert"
                            f" ses-average/fs_longitudinal/recon_template/mri/aparc+aseg.nonresected.mgz"
                            f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                            f" {dependencies_dir}/mrtrix3/labelconvert/{lut}.txt"
                            f" ses-average/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                            f" -force"
                            )
                            
                        # add surg_defect as label
                        run_command(f"mrcalc"
                            f" ses-average/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                            f" ses-average/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
                            f" -add"
                            f" ses-average/atlases/{side_type}/Desikan-Killiany_{suffix}.nii.gz"
                            f" -force"
                            )
                
                # If right-sided TLE, relabel right to ipsi and left to contra
                elif database.loc[sub,"side"] == "R":
                    for lut_suffix in [("fs_default_rh2ipsi_lh2contra","ipsi_contra"),("fs_default_rh2ipsi","ipsi"),("fs_default_lh2contra","contra")]:
                            lut, suffix = lut_suffix
                            
                            # generate atlas from nonresected aparc+aseg
                            run_command(f"labelconvert"
                                f" ses-average/fs_longitudinal/recon_template/mri/aparc+aseg.nonresected.mgz"
                                f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                                f" {dependencies_dir}/mrtrix3/labelconvert/{lut}.txt"
                                f" ses-average/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                                f" -force"
                                )
                                
                            # add surg_defect as label
                            run_command(f"mrcalc"
                                f" ses-average/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                                f" ses-average/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
                                f" -add"
                                f" ses-average/atlases/{side_type}/Desikan-Killiany_{suffix}.nii.gz"
                                f" -force"
                                )
                    
                else:
                    print("side for ipsi_contra atlas generation could not be determined")

    # Remove unneeded files
    tmp_files1 = glob(os.path.join(path, "ses-average", "atlases", 'tmp_*'))
    
    if surgical:
        tmp_files2 = glob(os.path.join(path, "ses-average", "atlases", "left_right", 'tmp_*'))
        tmp_files3 = glob(os.path.join(path, "ses-average", "atlases", "ipsi_contra", 'tmp_*'))
        tmp_files = tmp_files1 + tmp_files2 + tmp_files3
    else:
        tmp_files = tmp_files1
            
    for file in tmp_files:
        os.remove(file)
                
