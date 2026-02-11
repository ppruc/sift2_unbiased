import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def surg_defect(derivatives_dir,sub):

    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions

    # Create surg defect directory
    os.makedirs(os.path.join(path, "ses-average", "surg_defect"), exist_ok=True)

    for ses in sessions:
        
        # Despite being resampled to the same reference image, ITK errors may be raised due to (minor) numerical imprecisions within the image header ('images do not occupy same physical space'; conversion between software packages?); re-resamples to reference header to assure images headers match precisely
        run_command(f"antsApplyTransforms"
            f" -d 3"
            f" -i ses-average/template/outputs/T1w_Final_{ses}_resampled.nii.gz"
            f" -r ses-average/template/outputs/ants_refined_template0.nii.gz"
            f" -o ses-average/surg_defect/tmp_T1w_Final_{ses}_resampled.nii.gz"
            f" -n NearestNeighbor"
            )
            
        # Despite being resampled to the same reference image, ITK errors may be raised due to (minor) numerical imprecisions within the image header ('images do not occupy same physical space'; conversion between software packages?); re-resamples to reference header to assure images headers match precisely
        run_command(f"antsApplyTransforms"
            f" -d 3"
            f" -i ses-average/template/outputs/T1w_Final_{ses}_resampled_mask.nii.gz"
            f" -r ses-average/template/outputs/ants_refined_template0.nii.gz"
            f" -o ses-average/surg_defect/tmp_T1w_Final_resampled_mask_{ses}.nii.gz"
            f" -n NearestNeighbor"
            )
        
        # Perform N4 Bias Field Correction and Tissue Segmentation (GM, WM, CSF)
        #run_command(f"antsAtroposN4.sh"
            #f" -d 3"
            #f" -a ses-average/template/outputs/T1w_Final_{ses}_resampled.nii.gz"
            #f" -x ses-average/surg_defect/tmp_T1w_Final_resampled_mask_{ses}.nii.gz"
            #f" -o ses-average/surg_defect/tmp_T1w_Final_{ses}_resampled"
            #f" -c 3"
            #)
        
        # Perform Tissue Segmentation (GM, WM, CSF)
        run_command(f"Atropos"
            f" -d 3"
            f" -a ses-average/surg_defect/tmp_T1w_Final_{ses}_resampled.nii.gz"
            f" -x ses-average/surg_defect/tmp_T1w_Final_resampled_mask_{ses}.nii.gz"
            f" -o '[ses-average/surg_defect/tmp_T1w_Final_{ses}_resampledSegmentation.nii.gz,ses-average/surg_defect/tmp_T1w_Final_{ses}_resampledSegmentationPosteriors%d.nii.gz]'"
            f" -i 'KMeans[3]'"
            f" -m '[0.1,1x1x1]'"
            f" -c '[5,0.001]'"
            f" -r 1"
            f" -v"
            )
        
        # Smooth CSF segmentation
        run_command(f"mrfilter"
            f" ses-average/surg_defect/tmp_T1w_Final_{ses}_resampledSegmentationPosteriors1.nii.gz"
            f" smooth"
            f" ses-average/surg_defect/tmp_T1w_Final_{ses}_resampledSegmentationPosteriors1_smoothed.nii.gz"
            f" -force"
            )
    
    # Calculate intersection mask
    run_command(f"mrmath ses-average/surg_defect/tmp_T1w_Final_resampled_mask_{ses1}.nii.gz ses-average/surg_defect/tmp_T1w_Final_resampled_mask_{ses2}.nii.gz min ses-average/surg_defect/tmp_mask_intersection.nii.gz -force")
    
    # Calculate difference of CSF segmentations; prior smoothing migitates minor registration errors
    run_command(f"mrcalc"
        f" ses-average/surg_defect/tmp_T1w_Final_{ses2}_resampledSegmentationPosteriors1_smoothed.nii.gz"
        f" ses-average/surg_defect/tmp_T1w_Final_{ses1}_resampledSegmentationPosteriors1_smoothed.nii.gz"
        f" -sub"
        f" ses-average/surg_defect/tmp_csf_diff_smooth.nii.gz"
        f" -force"
        )
    
    # Exclude FOV differences
    run_command(f"mrcalc"
        f" ses-average/surg_defect/tmp_csf_diff_smooth.nii.gz"
        f" ses-average/surg_defect/tmp_mask_intersection.nii.gz"
        f" -mult"
        f" ses-average/surg_defect/tmp_tmp_csf_diff_smooth.nii.gz"
        f" -force"
        )
    
    # Exclude low probability voxels
    run_command(f"mrthreshold ses-average/surg_defect/tmp_tmp_csf_diff_smooth.nii.gz ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh.nii.gz -abs 0.2 -force")
    
    # Erode the mask to refine
    run_command(f"maskfilter ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh.nii.gz erode ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh_eroded.nii.gz -force")
    
    # Select the largest cluster of voxels
    run_command(f"maskfilter ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh_eroded.nii.gz connect ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh_eroded_largest.nii.gz -largest -force")
    
    # Dilate the mask to original size
    run_command(f"maskfilter ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh_eroded_largest.nii.gz dilate ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh_eroded_largest_clean.nii.gz -force")
    
    # Derive a preoperative tissue segmentation (GM + WM)
    run_command(f"mrcalc"
        f" ses-average/surg_defect/tmp_T1w_Final_{ses1}_resampledSegmentationPosteriors2.nii.gz"
        f" ses-average/surg_defect/tmp_T1w_Final_{ses1}_resampledSegmentationPosteriors3.nii.gz"
        f" -add"
        f" ses-average/surg_defect/tmp_preop_tissue.nii.gz"
        f" -force"
        )
     
    # Smooth the tissue segmentation
    run_command(f"mrfilter"
        f" ses-average/surg_defect/tmp_preop_tissue.nii.gz"
        f" smooth"
        f" ses-average/surg_defect/tmp_preop_tissue_smooth.nii.gz"
        f" -force"
        )
    
    # Exclude low probabilty voxels from tissue segmentation
    run_command(f"mrthreshold"
        f" ses-average/surg_defect/tmp_preop_tissue_smooth.nii.gz"
        f" ses-average/surg_defect/tmp_preop_tissue_smooth_thresh.nii.gz"
        f" -abs 0.2"
        f" -force"
        )
    
    # Limit the resection mask to only contain voxels classified as tissue in the preoperative image
    run_command(f"mrcalc"
        f" ses-average/surg_defect/tmp_tmp_csf_diff_smooth_thresh_eroded_largest_clean.nii.gz"
        f" ses-average/surg_defect/tmp_preop_tissue_smooth_thresh.nii.gz"
        " -mult ses-average/surg_defect/surg_defect_unsegmented.nii.gz"
        " -force"
        )
    
    # Run N4 Bias Field correction and resection zone subsegmentation (CSF, impaired GM)
    #run_command(f"antsAtroposN4.sh"
        #f" -d 3"
        #f" -a ses-average/template/outputs/T1w_Final_{ses2}_resampled.nii.gz"
        #f" -x ses-average/surg_defect/surg_defect_unsegmented.nii.gz"
        #f" -o ses-average/surg_defect/tmp_surg_defect_subseg"
        #f" -c 2"
        #)
    
    # Run resection zone subsegmentation (CSF, impaired GM)
    run_command(f"Atropos"
        f" -d 3"
        f" -a ses-average/surg_defect/tmp_T1w_Final_{ses2}_resampled.nii.gz"
        f" -x ses-average/surg_defect/surg_defect_unsegmented.nii.gz"
        f" -o '[ses-average/surg_defect/tmp_surg_defect_subsegSegmentation.nii.gz,ses-average/surg_defect/tmp_surg_defect_subsegSegmentationPosteriors%d.nii.gz']"
        f" -i 'KMeans[2]'"
        f" -m '[0.1,1x1x1]'"
        f" -c '[5,0.001]'"
        f" -r 1"
        f" -v"
        )
    
    # Refine subsegmentations (CSF, impaired GM)
    for posterior in ("Posteriors1", "Posteriors2"):
    
        c = "c1" if posterior == "Posteriors1" else "c2"
    
        # Exclude low probability voxels
        run_command(f"mrthreshold ses-average/surg_defect/tmp_surg_defect_subsegSegmentation{posterior}.nii.gz ses-average/surg_defect/tmp_surg_defect_subsegSegmentation{posterior}_thresh.nii.gz -abs 0.2 -force")
        # Erode the mask to refine
        run_command(f"maskfilter ses-average/surg_defect/tmp_surg_defect_subsegSegmentation{posterior}_thresh.nii.gz erode ses-average/surg_defect/tmp_surg_defect_subsegSegmentation{posterior}_thresh_eroded.nii.gz -force")
        # Select the largest cluster of voxels
        run_command(f"maskfilter ses-average/surg_defect/tmp_surg_defect_subsegSegmentation{posterior}_thresh_eroded.nii.gz connect ses-average/surg_defect/tmp_surg_defect_subsegSegmentation{posterior}_thresh_eroded_largest.nii.gz -largest -force")
        # Dilate mask to original size
        run_command(f"maskfilter ses-average/surg_defect/tmp_surg_defect_subsegSegmentation{posterior}_thresh_eroded_largest.nii.gz dilate ses-average/surg_defect/surg_defect_{c}.nii.gz -force")
    
    # Remove unneeded files
    run_command(f"rm ses-average/surg_defect/tmp_*")
