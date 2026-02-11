import os
import sys
from glob import glob
import pandas as pd
import nibabel as nib
import numpy as np
from mne.transforms import apply_trans

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

# return voxel coords of input vertex coords
def voxel_coordinates(vertex_coords,Torig):
    voxel_coords = (np.round(apply_trans(np.linalg.inv(Torig), vertex_coords))).astype(int) # for full voxel positions
    return voxel_coords

def atlas_session(derivatives_dir,dependencies_dir,sub,ses,surgical=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    print(path)
    
    os.makedirs(os.path.join(path, ses, "atlases"), exist_ok=True)

    # Relabel later resected tissue for ses1
    if not surgical:
    
                # generate atlas from nonresected aparc+aseg
                run_command(f"labelconvert"
                        f" {ses}/anat/recon/mri/aparc+aseg.mgz"
                        f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                        f" {dependencies_dir}/mrtrix3/labelconvert/fs_default.txt"
                        f" {ses}/atlases/Desikan-Killiany.nii.gz"
                        f" -force"
                        )
    
    else:
    
        # Create ipsi_contra atlas file
        database = pd.read_excel(f"{derivatives_dir}/../morgan_database.xlsx", index_col="sub")
    
        if ses == ses1:
        
                # Transform the surg defect to subject spaces
                run_command(f"mrtransform"
                    f" ses-average/surg_defect/surg_defect_final_dil.nii.gz"
                    f" {ses}/atlases/tmp_surg_defect_final.nii.gz"
                    f" -warp ses-average/transforms/{ses}/sub2temp_ants_deformation_inv.mif"
                    f" -template {ses}/anat/T1w_Final.nii.gz"
                    f" -interp Nearest"
                    f" -force"
                    )
                    
                #Resample surgical defect mask (ants_refined template space) to freesurfer resolution
                run_command(f"mri_vol2vol"
                    f" --mov {ses}/atlases/tmp_surg_defect_final.nii.gz"
                    f" --targ {ses}/anat/recon/mri/orig.mgz"
                    f" --o {ses}/atlases/tmp_surg_defect_final_fsspace.nii.gz"
                    f" --nearest"
                    f" --no-save-reg"
                    f" --regheader"
                    )
                
                # Invert the surg defect
                run_command(f"mrcalc 1"
                    f" {ses}/atlases/tmp_surg_defect_final_fsspace.nii.gz"
                    f" -sub"
                    f" {ses}/atlases/tmp_surg_defect_final_fsspace_inv.nii.gz"
                    f" -force"
                    )
                
                # Modify aseg file to exclude voxels
                run_command(f"mrcalc"
                    f" {ses}/anat/recon/mri/aseg.mgz"
                    f" {ses}/atlases/tmp_surg_defect_final_fsspace_inv.nii.gz"
                    f" -mult"
                    f" {ses}/anat/recon/mri/aseg.nonresected.mgz"
                    f" -force"
                    )
                    
                # Modify aseg file to include voxels
                run_command(f"mrcalc"
                    f" {ses}/anat/recon/mri/aseg.mgz"
                    f" {ses}/atlases/tmp_surg_defect_final_fsspace.nii.gz"
                    f" -mult"
                    f" {ses}/anat/recon/mri/aseg.resected.mgz"
                    f" -force"
                    )
                    
                ## Modify surface based measurements
                # load orig file
                t1 = nib.load(f"{ses}/anat/recon/mri/orig.mgz")

                # load torig (Vox2tkrRAS matrix)
                Torig = t1.header.get_vox2ras_tkr()
                
                # load surg_defect mask
                surg_defect = nib.load(f"{ses}/atlases/tmp_surg_defect_final_fsspace.nii.gz").get_fdata()

                # Modify annotation files of recon_template to exclude all vertices that lie within/without the surg_defect mask
                for hemi in ("lh","rh"):
                    
                    # load surface
                    surface_file = nib.freesurfer.read_geometry(f"{ses}/anat/recon/surf/{hemi}.white")
                    surface_coords_vertex, _ = surface_file
                        
                    # convert from surface RAS-tkr to voxel space
                    surface_coords_voxel = voxel_coordinates(surface_coords_vertex,Torig)
                    
                    # load annot file
                    labels, ctab, names = nib.freesurfer.io.read_annot(f"{ses}/anat/recon/label/{hemi}.aparc.annot")
                    
                    # re-assign all vertices that lie INSIDE the surg_defect mask to label "unknown", effectively excluding them from the analysis
                    nonresected_labels = labels.copy()
                    for i, voxel in enumerate(surface_coords_voxel):
                        if (0 <= voxel[0] < surg_defect.shape[0]) and (0 <= voxel[1] < surg_defect.shape[1]) and (0 <= voxel[2] < surg_defect.shape[2]):
                            if surg_defect[voxel[0], voxel[1], voxel[2]] == 1:
                                nonresected_labels[i] = -1
                    
                    # save modified annotations (hemispheres annotations, vertices within surg_defect excluded)
                    nib.freesurfer.io.write_annot(f"{ses}/anat/recon/label/{hemi}.aparc.nonresected.annot", nonresected_labels, ctab, names)
                    
                    # re-assign all vertices that lie OUTSIDE the surg_defect mask to label "unknown", effectively excluding them from the analysis
                    resected_labels = labels.copy()
                    for i, voxel in enumerate(surface_coords_voxel):
                        if (0 <= voxel[0] < surg_defect.shape[0]) and (0 <= voxel[1] < surg_defect.shape[1]) and (0 <= voxel[2] < surg_defect.shape[2]):
                            if surg_defect[voxel[0], voxel[1], voxel[2]] == 0:
                                resected_labels[i] = -1
                        
                    # save modified inverse annotation (surgical defect annotation, vertices outside excluded)
                    nib.freesurfer.io.write_annot(f"{ses}/anat/recon/label/{hemi}.aparc.resected.annot", resected_labels, ctab, names)
            
                # Generate corrected aparc+aseg for nonresected.annot and nonresected aseg files
                run_command(f"mri_surf2volseg"
                    f" --o {ses}/anat/recon/mri/aparc+aseg.nonresected.mgz"
                    f" --label-cortex"
                    f" --i {ses}/anat/recon/mri/aseg.nonresected.mgz"
                    f" --threads 96"
                    f" --lh-annot {ses}/anat/recon/label/lh.aparc.nonresected.annot 1000"
                    f" --lh-cortex-mask {ses}/anat/recon/label/lh.cortex.label"
                    f" --lh-white {ses}/anat/recon/surf/lh.white"
                    f" --lh-pial {ses}/anat/recon/surf/lh.pial"
                    f" --rh-annot {ses}/anat/recon/label/rh.aparc.nonresected.annot 2000"
                    f" --rh-cortex-mask {ses}/anat/recon/label/rh.cortex.label"
                    f" --rh-white {ses}/anat/recon/surf/rh.white"
                    f" --rh-pial {ses}/anat/recon/surf/rh.pial"
                    )
                    
                # Generate corrected aparc+aseg for resected.annot and resected aseg files
                run_command(f"mri_surf2volseg"
                    f" --o {ses}/anat/recon/mri/aparc+aseg.resected.mgz"
                    f" --label-cortex"
                    f" --i {ses}/anat/recon/mri/aseg.resected.mgz"
                    f" --threads 96"
                    f" --lh-annot {ses}/anat/recon/label/lh.aparc.resected.annot 1000"
                    f" --lh-cortex-mask {ses}/anat/recon/label/lh.cortex.label"
                    f" --lh-white {ses}/anat/recon/surf/lh.white"
                    f" --lh-pial {ses}/anat/recon/surf/lh.pial"
                    f" --rh-annot {ses}/anat/recon/label/rh.aparc.resected.annot 2000"
                    f" --rh-cortex-mask {ses}/anat/recon/label/rh.cortex.label"
                    f" --rh-white {ses}/anat/recon/surf/rh.white"
                    f" --rh-pial {ses}/anat/recon/surf/rh.pial"
                    )
                    
                # Create a label file for the surg defect with unique identifier (86)
                run_command(f"labelconvert"
                    f" {ses}/anat/recon/mri/aparc+aseg.resected.mgz"
                    f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                    f" {dependencies_dir}/mrtrix3/labelconvert/fs_default.txt"
                    f" {ses}/atlases/tmp_Desikan-Killiany_resected.nii.gz"
                    f" -force"
                    )
                    
                run_command(f"mrthreshold"
                    f" {ses}/atlases/tmp_Desikan-Killiany_resected.nii.gz"
                    f" {ses}/atlases/tmp_Desikan-Killiany_resected_thr.nii.gz"
                    f" -abs 0.01"
                    f" -force"
                    )
                
                run_command(f"mrcalc"
                    f" {ses}/atlases/tmp_Desikan-Killiany_resected_thr.nii.gz"
                    f" 1"
                    f" 86"
                    f" -replace"
                    f" {ses}/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
                    f" -force"
                    )
            
        # Create output directory
        for side_type in ("left_right", "ipsi_contra"):
            
                os.makedirs(os.path.join(path, ses, "atlases", side_type), exist_ok=True)
                    
            
                if side_type == "left_right":
                    
                        # Create atlas file
                        for lut_suffix in [("fs_default","left_right"),("fs_default_lh","left"),("fs_default_rh","right")]:
                            lut, suffix = lut_suffix
                            
                            # generate atlas from nonresected aparc+aseg
                            run_command(f"labelconvert"
                                f" {ses}/anat/recon/mri/aparc+aseg{'.nonresected' if ses == ses1 else ''}.mgz"
                                f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                                f" {dependencies_dir}/mrtrix3/labelconvert/{lut}.txt"
                                f" {ses}/atlases/{side_type}/{'tmp_' if ses == ses1 else ''}Desikan-Killiany_{suffix}.nii.gz"
                                f" -force"
                                )
                            
                            if ses == ses1:
                                # add surg_defect as label
                                run_command(f"mrcalc"
                                    f" {ses}/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                                    f" {ses}/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
                                    f" -add"
                                    f" {ses}/atlases/{side_type}/Desikan-Killiany_{suffix}.nii.gz"
                                    f" -force"
                                    )
                  
                else:
                        # If left-sided TLE, relabel left to ipsi and right to contra
                        if database.loc[sub,"side"] == "L":
                            for lut_suffix in [("fs_default_lh2ipsi_rh2contra","ipsi_contra"),("fs_default_lh2ipsi","ipsi"),("fs_default_rh2contra","contra")]:
                                lut, suffix = lut_suffix
                                
                                # generate atlas from nonresected aparc+aseg
                                run_command(f"labelconvert"
                                    f" {ses}/anat/recon/mri/aparc+aseg{'.nonresected' if ses == ses1 else ''}.mgz"
                                    f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                                    f" {dependencies_dir}/mrtrix3/labelconvert/{lut}.txt"
                                    f" {ses}/atlases/{side_type}/{'tmp_' if ses == ses1 else ''}Desikan-Killiany_{suffix}.nii.gz"
                                    f" -force"
                                    )
                                
                                if ses == ses1:
                                    # add surg_defect as label
                                    run_command(f"mrcalc"
                                        f" {ses}/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                                        f" {ses}/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
                                        f" -add"
                                        f" {ses}/atlases/{side_type}/Desikan-Killiany_{suffix}.nii.gz"
                                        f" -force"
                                        )
                        
                        # If right-sided TLE, relabel right to ipsi and left to contra
                        elif database.loc[sub,"side"] == "R":
                            for lut_suffix in [("fs_default_rh2ipsi_lh2contra","ipsi_contra"),("fs_default_rh2ipsi","ipsi"),("fs_default_lh2contra","contra")]:
                                    lut, suffix = lut_suffix
                                    
                                    # generate atlas from nonresected aparc+aseg
                                    run_command(f"labelconvert"
                                        f" {ses}/anat/recon/mri/aparc+aseg{'.nonresected' if ses == ses1 else ''}.mgz"
                                        f" {dependencies_dir}/mrtrix3/labelconvert/FreeSurferColorLUT.txt"
                                        f" {dependencies_dir}/mrtrix3/labelconvert/{lut}.txt"
                                        f" {ses}/atlases/{side_type}/{'tmp_' if ses == ses1 else ''}Desikan-Killiany_{suffix}.nii.gz"
                                        f" -force"
                                        )
                                    
                                    if ses == ses1:
                                        # add surg_defect as label
                                        run_command(f"mrcalc"
                                            f" {ses}/atlases/{side_type}/tmp_Desikan-Killiany_{suffix}.nii.gz"
                                            f" {ses}/atlases/tmp_Desikan-Killiany_surg_defect_label.nii.gz"
                                            f" -add"
                                            f" {ses}/atlases/{side_type}/Desikan-Killiany_{suffix}.nii.gz"
                                            f" -force"
                                            )
                            
                        else:
                            print("TLE_Side for ipsi_contra atlas generation could not be determined")


                    
                
    # Remove unneeded files
    
    if surgical and ses == ses1:
        tmp_files1 = glob(os.path.join(path, ses, "atlases", 'tmp_*'))
        tmp_files2 = glob(os.path.join(path, ses1, "atlases", "left_right", 'tmp_*'))
        tmp_files3 = glob(os.path.join(path, ses1, "atlases", "ipsi_contra", 'tmp_*'))
        tmp_files = tmp_files1 + tmp_files2 + tmp_files3
            
        for file in tmp_files:
            os.remove(file)
