import sys
import os
import numpy as np
import pandas as pd


path =  "/Users/user/Downloads/sift2_unbiased"
functions = os.path.join(path, "code", "dependencies", "functions") 
sys.path.append(os.path.abspath(functions))

from run_command import run_command

cmd_fixelcorrespondence = "/Users/user/Documents/github/mrtrix3_fixelcorrespondence/bin/fixelcorrespondence"
cmd_fixel2fixel = "/Users/user/Documents/github/mrtrix3_fixelcorrespondence/bin/fixel2fixel"

def true_bundles(matrix_path):
    """
    Given a path to a symmetric matrix CSV file, return non-zero edges (i+1, j+1) excluding diagonal and duplicates.
    """
    matrix = pd.read_csv(matrix_path, header=None).values  # Load and convert to numpy array
    nonzero_edges = set()
    n_rows, n_cols = matrix.shape
    for i in range(n_rows):
        for j in range(i+1, n_cols):  # only upper triangle
            if matrix[i, j] != 0:
                edge = (i + 1, j + 1)
                nonzero_edges.add(edge)
    return sorted(nonzero_edges)

def filter_tractogram(tractogram_in_path, assignments_path, bundle_list, tractogram_out_path, orig_path):
    """
    Extracts and filters streamlines from a tractogram based on a list of bundle pairs.
    
    Parameters:
        tractogram_path (str): Path to the input tractogram.
        assignments_path (str): Path to the streamline-to-parcel assignments file.
        bundle_list (list of tuple): List of (i, j) tuples indicating bundles to keep.
        output_path (str): Directory where filtered tractogram and intermediate files are stored.
    """

    output_path = os.path.dirname(tractogram_out_path)
    tractogram_name = os.path.splitext(os.path.basename(tractogram_out_path))[0]

    os.makedirs(output_path, exist_ok=True)
    for bundle in bundle_list:
        i,j = bundle
        run_command(
            f"connectome2tck {tractogram_in_path} {assignments_path} {output_path}/tmp_edge_{i}_{j}.tck -nodes {i},{j} -exclusive -files single"
        )
    
    run_command(f"tckedit {output_path}/tmp_edge_* {tractogram_out_path} -force")
    
    run_command(f"tck2connectome {tractogram_out_path} {orig_path}/segmentations/gm_parcels.nii.gz {output_path}/tpm_edge_connectome.csv -out_assignments {output_path}/{tractogram_name}_assignments.txt -force")
    run_command(f"rm {output_path}/tmp_edge_*")


def prepare_phantoms(phantom_path, params_path, n_tcks=20000, output_path=None, impute_template=False):
    """
    Prepare longitudinal diffusion MRI phantoms for quantitative tractography analysis.

    This function performs end-to-end processing of two phantom timepoints (tp1, tp2),
    including:
    - DWI conversion to mif
    - multi-tissue response estimation, FOD reconstruction,
    - tractogram generation, generation of a ground truth*, fixel correspondence,
    - and computation of longitudinal fibre density (FD) mean and difference maps.
    - Template and cross-sectional tractograms are generated
    - tractograms additionally filtered to retain only true streamlines. 
    - For lesion phantom, template FODs can be imputed from first session within the lesion mask to derive intact template

    * only if a non-noisy phantom is provided; ground truth results must be copied manually into directory of noisy phantoms to orig/ground_truth/

    """
    
    timpoints = ["tp1","tp2"]

    orig_path = os.path.join(phantom_path,"orig")
    os.chdir(orig_path)
            
    for tp in timpoints:

        # Create output folder
        os.makedirs(f"{output_path}/{tp}", exist_ok=True)
        
        # Derive odfs
        run_command(f"mrconvert {orig_path}/{tp}/b*.nii.gz {output_path}/{tp}/dwi.mif -fslgrad {params_path}/simulation_disco_bvecs_xinverted.txt {params_path}/simulation_disco_bvals.txt -force")
    
    os.makedirs(f"{orig_path}/response_functions/", exist_ok=True)
    
    run_command(f"dwi2response dhollander"
            f" {output_path}/tp1/dwi.mif"
            f" {orig_path}/response_functions/wm.txt"
            f" {orig_path}/response_functions/gm.txt"
            f" {orig_path}/response_functions/csf.txt"
            f" -voxels {orig_path}/response_functions/voxels.mif"
            f" -force"
            )
            
    for tp in timpoints:

        run_command(f"dwi2fod msmt_csd"
            f" {output_path}/{tp}/dwi.mif"
            f" {orig_path}/response_functions/wm.txt"
            f" {output_path}/{tp}/wmfod.mif"
            f" {orig_path}/response_functions/csf.txt"
            f" {output_path}/{tp}/csffod.mif"
            f" -force"
            )
        
        run_command(f"mtnormalise {output_path}/{tp}/wmfod.mif {output_path}/{tp}/wmfod_norm.mif.gz {output_path}/{tp}/csffod.mif {output_path}/{tp}/csffod_norm.mif -mask {orig_path}/segmentations/wm_segm.nii.gz -force")
        
        # Generate tractogram
        run_command(f"tckgen"
            f" -seed_gmwm {orig_path}/segmentations/gmwm.mif"
            f" -act {orig_path}/segmentations/5tt.mif"
            f" -select {n_tcks}"
            f" {output_path}/{tp}/wmfod_norm.mif.gz"
            f" {output_path}/{tp}/tracks.tck"
            f" -backtrack"
            f" -force"
            )
                
        
        if "snr" in phantom_path:
            print("not generating groundtruth; noisy phantom")
        else:
            # Derive groundtruth mu without optimisation
            run_command(f"tcksift2 {orig_path}/ground_truth/tp{'1' if tp == 'tp1' else '2'}/tracks_gt_{tp}.tck"
                f" {output_path}/{tp}/wmfod_norm.mif.gz"
                f" -max_iters 0"
                f" {orig_path}/ground_truth/tp{'1' if tp == 'tp1' else '2'}/gt_sift2_{tp}.txt"
                f" -out_mu {orig_path}/ground_truth/tp{'1' if tp == 'tp1' else '2'}/gt_sift2_mu.txt"
                f" -reg_tv 1000000000000000000000000000000000000000" # overregularising to so optimiser does not converge
                f" -force"
                )
                    
            # Derive groundtruth fiber count connectome
            run_command(f"tck2connectome {orig_path}/ground_truth/tp{'1' if tp == 'tp1' else '2'}/tracks_gt_{tp}.tck"
                f" {orig_path}/segmentations/gm_parcels.nii.gz"
                f" {orig_path}/ground_truth/tp{'1' if tp == 'tp1' else '2'}/gt_sift2_{tp}.csv"
                f" -symmetric"
                f" -force"
                )
            
            os.makedirs(f"{orig_path}/ground_truth_fbc/tp{tp}", exist_ok=True)
            
            # Derive groundtruth fbc
            run_command(f"tcksift2 {orig_path}/ground_truth/tp{'1' if tp == 'tp1' else '2'}/tracks_gt_{tp}.tck"
                f" {output_path}/{tp}/wmfod_norm.mif.gz"
                f" {orig_path}/ground_truth_fbc/tp{'1' if tp == 'tp1' else '2'}/gt_sift2_{tp}.txt"
                f" -out_mu {orig_path}/ground_truth_fbc/tp{'1' if tp == 'tp1' else '2'}/gt_sift2_mu.txt"
                f" -force"
                )
            
            # Derive groundtruth FBC connectome
            run_command(f"tck2connectome {orig_path}/ground_truth/tp{'1' if tp == 'tp1' else '2'}/tracks_gt_{tp}.tck"
                f" {orig_path}/segmentations/gm_parcels.nii.gz"
                f" {orig_path}/ground_truth_fbc/tp{'1' if tp == 'tp1' else '2'}/gt_sift2_{tp}.csv"
                f" -tck_weights_in {orig_path}/ground_truth_fbc/tp{'1' if tp == 'tp1' else '2'}/gt_sift2_{tp}.txt"
                f" -symmetric"
                f" -force"
                )
        
    # Define tps
    tp1 = os.path.join(output_path, f"tp1/")
    tp2 = os.path.join(output_path, f"tp2/")
    tp_av = os.path.join(output_path, f"tp_average/")

    # Create average folder
    os.makedirs(tp_av, exist_ok=True)

    if impute_template:
        run_command(f"maskfilter {orig_path}/segmentations/lesion.nii.gz dilate {orig_path}/segmentations/lesion_dil.nii.gz -npass 2 -force")
        run_command(f"mrcalc 1 {orig_path}/segmentations/lesion_dil.nii.gz -sub {orig_path}/segmentations/lesion_dil_inv.nii.gz -force")
        run_command(f"mrcalc {tp2}/wmfod_norm.mif.gz {orig_path}/segmentations/lesion_dil_inv.nii.gz -div {tp2}/wmfod_norm.mif.gz -force")
        
    run_command(f"mrmath {tp1}/wmfod_norm.mif.gz {tp2}/wmfod_norm.mif.gz mean {tp_av}/wmfod_norm_mean.mif.gz -force")
    run_command(f"rm -r {output_path}/fixels/")
    run_command(f"rm -r {output_path}/fixels/fixel_mask/")
    run_command(f"rm -r {output_path}/fixels/fd/")
    run_command(f"mkdir -p {output_path}/fixels/fd")
    run_command(f"fod2fixel -mask {orig_path}/segmentations/wm_segm.nii.gz -fmls_peak_value 0.06 {tp_av}/wmfod_norm_mean.mif.gz {output_path}/fixels/fixel_mask -afd fd.mif -maxnum 4 -force")
    
    for tp in ("tp1", "tp2"):
        run_command(f"fod2fixel -mask {orig_path}/segmentations/wm_segm.nii.gz {output_path}/{tp}/wmfod_norm.mif.gz {output_path}/fixels/{tp} -afd fd.mif -maxnum 5 -force")
    
    run_command(f"cp {output_path}/fixels/fixel_mask/index.mif {output_path}/fixels/fixel_mask/directions.mif {output_path}/fixels/fd/")
    
    for tp in ("tp1", "tp2"):
        run_command(f"{cmd_fixelcorrespondence} {output_path}/fixels/{tp}/fd.mif {output_path}/fixels/fixel_mask/fd.mif {output_path}/fixels/fixel_mask/{tp}_to_template -algorithm in2023 -force")

        run_command(f"{cmd_fixel2fixel} {output_path}/fixels/{tp}/fd.mif {output_path}/fixels/fixel_mask/{tp}_to_template sum {output_path}/fixels/fd/ {tp}.mif -force")
        
    # Mean
    run_command(f"mrmath {output_path}/fixels/fd/tp2.mif {output_path}/fixels/fd/tp1.mif mean {output_path}/fixels/fd/tp1_tp2_mean.mif -force")
        
    # Difference
    run_command(f"mrcalc {output_path}/fixels/fd/tp2.mif {output_path}/fixels/fd/tp1.mif -sub {output_path}/fixels/fd/tp2_min_tp1.mif -force")
    run_command(f"mrcalc {output_path}/fixels/fd/tp1.mif {output_path}/fixels/fd/tp2.mif -sub {output_path}/fixels/fd/tp1_min_tp2.mif -force")
    
    # Half Difference
    run_command(f"mrcalc {output_path}/fixels/fd/tp2_min_tp1.mif 2 -div {output_path}/fixels/fd/tp2_min_tp1_half.mif -force")
    run_command(f"mrcalc {output_path}/fixels/fd/tp1_min_tp2.mif 2 -div {output_path}/fixels/fd/tp1_min_tp2_half.mif -force")
    
    # Generate Combined/Template Tractograms
    tcks_tp1 = f"{tp1}/tracks.tck"
    tcks_tp2 = f"{tp2}/tracks.tck"
    run_command(f"tckedit {tcks_tp1} {tcks_tp2} {tp_av}/tmp_tracks_combined.tck -force")
    run_command(f"tckedit {tp_av}/tmp_tracks_combined.tck {tp_av}/tracks_combined.tck -number {n_tcks} -force")
    run_command(f"tckgen"
        f" -seed_gmwm {orig_path}/segmentations/gmwm.mif"
        f" -act {orig_path}/segmentations/5tt.mif"
        f" -select {n_tcks}"
        f" {tp_av}/wmfod_norm_mean.mif.gz"
        f" {tp_av}/tracks_template.tck"
        f" -backtrack"
        f" -force")
    
    # Generate streamline assignments
    for tp in (tp1, tp2):
        run_command(f"tck2connectome {tp}/tracks.tck {orig_path}/segmentations/gm_parcels.nii.gz {tp}/tmp.csv -out_assignments {tp}/tracks_assignments.txt -force")

    # Create groundtruth tcks and assignment files
    run_command(f"tck2connectome {tp_av}/tracks_combined.tck {orig_path}/segmentations/gm_parcels.nii.gz {tp_av}/tmp.csv -out_assignments {tp_av}/tracks_combined_assignments.txt -force")
    run_command(f"tck2connectome {tp_av}/tracks_template.tck {orig_path}/segmentations/gm_parcels.nii.gz {tp_av}/tmp.csv -out_assignments {tp_av}/tracks_template_assignments.txt -force")
    run_command(f"tck2connectome {orig_path}/ground_truth/tp1/tracks_gt_tp1.tck {orig_path}/segmentations/gm_parcels.nii.gz {tp_av}/tmp.csv -out_assignments {orig_path}/ground_truth/tp1/tracks_gt_tp1_assignments.txt -force")
    run_command(f"rm {tp_av}/tmp.csv")

    # filter tractograms
    ground_truth_bundles = true_bundles(f"{orig_path}/ground_truth/tp1/gt_sift2_tp1.csv")
    print("ground truth bundles:")
    print(ground_truth_bundles)
    
    filter_tractogram(
        tractogram_in_path=f"{tp_av}/tracks_template.tck",
        assignments_path=f"{tp_av}/tracks_template_assignments.txt",
        bundle_list=ground_truth_bundles,
        tractogram_out_path=f"{tp_av}/tracks_template_filtered.tck",
        orig_path=orig_path
    )

    filter_tractogram(
        tractogram_in_path=f"{tp_av}/tracks_combined.tck",
        assignments_path=f"{tp_av}/tracks_combined_assignments.txt",
        bundle_list=ground_truth_bundles,
        tractogram_out_path=f"{tp_av}/tracks_combined_filtered.tck",
        orig_path=orig_path

    ) 

    filter_tractogram(
        tractogram_in_path=f"{tp1}/tracks.tck",
        assignments_path=f"{tp1}/tracks_assignments.txt",
        bundle_list=ground_truth_bundles,
        tractogram_out_path=f"{tp1}/tracks_filtered.tck",
        orig_path=orig_path

    ) 

    filter_tractogram(
        tractogram_in_path=f"{tp2}/tracks.tck",
        assignments_path=f"{tp2}/tracks_assignments.txt",
        bundle_list=ground_truth_bundles,
        tractogram_out_path=f"{tp2}/tracks_filtered.tck",
        orig_path=orig_path
    ) 

    # Extract b0 image
    #run_command(f"dwiextract {tp}/dwi.mif {tp}/tmp_b0.nii.gz -bzero -force")
    #run_command(f"mrmath {tp}/tmp_b0.nii.gz mean {tp}/b0.nii.gz -axis 3 -force")
   
    

