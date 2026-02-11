import os
import sys
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


def anatomical_stats_modified(derivatives_dir, sub, dependencies_dir):

    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    print(path)
    
    # Set subject directory
    os.environ["SUBJECTS_DIR"] = f"{path}/ses-average/fs_longitudinal" #export SINGULARITYENV_SUBJECTS_DIR={ses} # if run on server
    
    ## Modify volume based measurments
    # Transform surgical defect from ants refined template space to subject in freesurfer template space
    for ses in sessions:
        
        run_command(f"warpinvert ses-average/transforms/{ses}/temp_rigid2temp_ants_deformation.mif ses-average/transforms/{ses}/temp_rigid2temp_ants_deformation_inv.mif -force")
        
        run_command(f"mrtransform"
            f" ses-average/surg_defect/surg_defect_final_dil.nii.gz"
            f" ses-average/fs_longitudinal/surg_defect_final_dil_{ses}.nii.gz"
            f" -warp ses-average/transforms/{ses}/temp_rigid2temp_ants_deformation_inv.mif"
            f" -template ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/norm.mgz"
            f" -interp nearest"
            f" -force"
            )
        
        # Invert the surg defect mask (timepoint 1 only)
        run_command(f"mrcalc"
            f" 1"
            f" ses-average/fs_longitudinal/surg_defect_final_dil_{ses}.nii.gz"
            f" -sub"
            f" ses-average/fs_longitudinal/surg_defect_final_dil_{ses}_inv.nii.gz"
            f" -force"
            )
            
        # loop over relevant files
        for file in ("aseg","norm","brainmask"):
            
            # Exclude all voxels that are part of the resection cavity (both timepoints)
            run_command(f"mrcalc"
                f" ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/{file}.mgz"
                f" ses-average/fs_longitudinal/surg_defect_final_dil_{ses}_inv.nii.gz"
                f" -mult"
                f" ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/{file}.nonresected.mgz"
                f" -force"
                )
                
            # Include all voxels that are part of the resection cavity (timepoint 1 only)
            if ses == ses1:
                run_command(f"mrcalc"
                    f" ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/{file}.mgz"
                    f" ses-average/fs_longitudinal/surg_defect_final_dil_{ses}.nii.gz"
                    f" -mult"
                    f" ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/{file}.resected.mgz"
                    f" -force"
                    )
                        
    # Create voxel based anatomical stats for non-resected parcels
    for ses in sessions:
        run_command(f"mri_segstats"
            f" --seed 1234"
            f" --seg ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/aseg.nonresected.mgz"
            f" --sum ses-average/fs_longitudinal/recon_{ses}.long.recon_template/stats/aseg.nonresected.stats"
            f" --pv ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/norm.nonresected.mgz"
            f" --empty"
            f" --brainmask ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/brainmask.nonresected.mgz"
            f" --brain-vol-from-seg"
            f" --excludeid 0"
            f" --excl-ctxgmwm"
            f" --supratent"
            f" --subcortgray"
            f" --in ses-average/fs_longitudinal/recon_{ses}.long.recon_template/mri/norm.nonresected.mgz"
            f" --in-intensity-name norm.nonresected"
            f" --in-intensity-units MR"
            f" --etiv"
            f" --surf-wm-vol"
            f" --surf-ctx-vol"
            f" --totalgray"
            f" --ctab {dependencies_dir}/freesurfer/ASegStatsLUT.txt"
            f" --subject recon_{ses}.long.recon_template"
            )
    
    # Create voxel based anatomical stats based for resected parcels
    run_command(f"mri_segstats"
        f" --seed 1234"
        f" --seg ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/mri/aseg.resected.mgz"
        f" --sum ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/stats/aseg.resected.stats"
        f" --pv ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/mri/norm.resected.mgz"
        f" --empty"
        f" --brainmask ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/mri/brainmask.resected.mgz"
        f" --brain-vol-from-seg"
        f" --excludeid 0"
        f" --excl-ctxgmwm"
        f" --supratent"
        f" --subcortgray"
        f" --in ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/mri/norm.resected.mgz"
        f" --in-intensity-name norm.resected"
        f" --in-intensity-units MR"
        f" --etiv"
        f" --surf-wm-vol"
        f" --surf-ctx-vol"
        f" --totalgray"
        f" --ctab {dependencies_dir}/freesurfer/ASegStatsLUT.txt"
        f" --subject recon_{ses1}.long.recon_template"
        )
    
    ## Modify surface based measurements (both timepoints have vertex correspondence, template edit sufficient)
    # Resample surgical defect mask (ants_refined template space) to freesurfer resolution
    run_command(f"mri_vol2vol"
                    f" --mov ses-average/surg_defect/surg_defect_final_dil.nii.gz"
                    f" --targ ses-average/fs_longitudinal/recon_template/mri/orig.mgz"
                    f" --o ses-average/fs_longitudinal/surg_defect_final_dil_ses-average.nii.gz"
                    f" --nearest"
                    f" --no-save-reg"
                    f" --regheader"
                    )
    
    # load orig file
    t1 = nib.load("ses-average/fs_longitudinal/recon_template/mri/orig.mgz")

    # load torig (Vox2tkrRAS matrix)
    Torig = t1.header.get_vox2ras_tkr()
    
    # load surg_defect mask
    surg_defect = nib.load("ses-average/fs_longitudinal/surg_defect_final_dil_ses-average.nii.gz").get_fdata()

    # Modify annotation files of recon_template to exclude all vertices that lie within/without the surg_defect mask
    for hemi in ("lh","rh"):
        
        # load surface
        surface_file = nib.freesurfer.read_geometry(f"ses-average/fs_longitudinal/recon_template/surf/{hemi}.white")
        surface_coords_vertex, _ = surface_file
            
        # convert from surface RAS-tkr to voxel space
        surface_coords_voxel = voxel_coordinates(surface_coords_vertex,Torig)
        
        # load annot file
        labels, ctab, names = nib.freesurfer.io.read_annot(f"ses-average/fs_longitudinal/recon_template/label/{hemi}.aparc.annot")
        
        # re-assign all vertices that lie INSIDE the surg_defect mask to label "unknown", effectively excluding them from the analysis
        nonresected_labels = labels.copy()
        for i, voxel in enumerate(surface_coords_voxel):
            if (0 <= voxel[0] < surg_defect.shape[0]) and (0 <= voxel[1] < surg_defect.shape[1]) and (0 <= voxel[2] < surg_defect.shape[2]):
                if surg_defect[voxel[0], voxel[1], voxel[2]] == 1:
                    nonresected_labels[i] = -1
        
        # save modified annotations (hemispheres annotations, vertices within surg_defect excluded)
        nib.freesurfer.io.write_annot(f"ses-average/fs_longitudinal/recon_template/label/{hemi}.aparc.nonresected.annot", nonresected_labels, ctab, names)
        
    
        # re-assign all vertices that lie OUTSIDE the surg_defect mask to label "unknown", effectively excluding them from the analysis
        resected_labels = labels.copy()
        for i, voxel in enumerate(surface_coords_voxel):
            if (0 <= voxel[0] < surg_defect.shape[0]) and (0 <= voxel[1] < surg_defect.shape[1]) and (0 <= voxel[2] < surg_defect.shape[2]):
                if surg_defect[voxel[0], voxel[1], voxel[2]] == 0:
                    resected_labels[i] = -1
            
        # save modified inverse annotation (surgical defect annotation, vertices outside excluded)
        nib.freesurfer.io.write_annot(f"ses-average/fs_longitudinal/recon_template/label/{hemi}.aparc.resected.annot", resected_labels, ctab, names)
    
    
    # Create surface based anatomical stats based for non-resected and resected parcels
    for ses in sessions:
        for hemi in ("lh","rh"):
            run_command(f"mris_anatomical_stats"
                f" -th3"
                f" -mgz"
                f" -b"
                f" -cortex ses-average/fs_longitudinal/recon_template/label/{hemi}.cortex.label" # define which vertices are cortex
                f" -a ses-average/fs_longitudinal/recon_template/label/{hemi}.aparc.nonresected.annot" # define label number/color/name for vertices
                f" -t ses-average/fs_longitudinal/recon_{ses}.long.recon_template/surf/{hemi}.thickness" # define thickness file to use for ThickAvg calc
                f" -c ses-average/fs_longitudinal/recon_{ses}.long.recon_template/label/aparc.annot.ctab" # define LUT output
                f" -f ses-average/fs_longitudinal/recon_{ses}.long.recon_template/stats/{hemi}.aparc.nonresected.stats" # define stats output
                f" recon_{ses}.long.recon_template"
                f" {hemi}"
                )
    
    # Create surface-based anatomical stats for resected parcels
    for hemi in ("lh","rh"):
        run_command(f"mris_anatomical_stats"
            f" -th3"
            f" -mgz"
            f" -b"
            f" -cortex ses-average/fs_longitudinal/recon_template/label/{hemi}.cortex.label" # define which vertices are cortex
            f" -a ses-average/fs_longitudinal/recon_template/label/{hemi}.aparc.resected.annot" # define label number/color/name for vertices
            f" -t ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/surf/{hemi}.thickness" # define thickness file to use for ThickAvg calc
            f" -c ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/label/aparc.annot.ctab" # define LUT output
            f" -f ses-average/fs_longitudinal/recon_{ses1}.long.recon_template/stats/{hemi}.aparc.resected.stats" # define stats output
            f" recon_{ses1}.long.recon_template"
            f" {hemi}"
            )
