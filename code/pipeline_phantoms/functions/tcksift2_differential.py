import sys
import os

repository_path = "/Users/user/Downloads/sift2_unbiased/"
functions = os.path.join(repository_path, "code", "dependencies", "functions") 
sys.path.append(os.path.abspath(functions))

from run_command import run_command

tcksift2_cmd = "/Users/user/Documents/github/mrtrix3_sift2diff/bin/tcksift2"

def tcksift2_differential(phantom_path, input_path, tcks, reg_basis_abs, reg_fn_abs, reg_strength_abs, reg_basis_diff, reg_strength_diff, reg_fn_diff, min_iters=10, debug=False):
    """
    Perform differential SIFT2 optimisation.

    Parameters
    ----------
    phantom_path : str
        Path to the phantom data directory.
    input_path : str
        Path to the input data directory.
    tcks : str
        Identifier for the tractogram to process.
    reg_basis_abs : str
        Regularisation basis order for the absolute component.
    reg_fn_abs : str
        Regularisation function for the absolute component.
    reg_strength_abs : float
        Regularisation strength for the absolute component.
    reg_basis_diff : str
        Regularisation basis order for the differential component.
    reg_strength_diff : float
        Regularisation strength for the differential component.
    reg_fn_diff : str
        Regularisation function for the differential component.
    debug : bool, optional
        Whether to output debug information (default is False).

    Outputs
    -------
    - Absolute streamline weights (sift2_weights.txt)
    - Differential streamline weights (sift2diff_weights.txt)
    - Absolute coefficients (sift2_coeffs.txt)
    - Mu values (sift2_mu.txt)
    - Algorithm convergence CSV (algorithm_convergence.csv)
    - Connectomes for absolute and differential weights (connectome.csv, connectome_diff_half.csv)

    """
        
    # Define Paths
    orig_path = os.path.join(phantom_path,"orig")
    output_path = f"{input_path}/sift2_differential/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/reg_diff_{reg_strength_diff}/"
    os.makedirs(output_path, exist_ok=True)
    
    if debug:
        debug_option = f"-output_debug {output_path}/debug"
        
    if tcks == "tracks_groundtruth":
        input_tcks = f"{phantom_path}/orig/ground_truth/tp1/tracks_gt_tp1.tck"
        input_tcks_assignments = f"{phantom_path}/orig/ground_truth/tp1/tracks_gt_tp1_assignments.txt"
    else:
        input_tcks = f"{input_path}/tp_average/{tcks}.tck"
        input_tcks_assignments = f"{input_path}/tp_average/{tcks}_assignments.txt"
    
    # run SIFT2diff
    run_command(f"{tcksift2_cmd}"
        f" {input_tcks}"
        f" {input_path}/fixels/fd/tp1_tp2_mean.mif"
        f" {output_path}/sift2_weights.txt"
        f" -act {orig_path}/segmentations/5tt.mif*"
        f" -reg_basis_abs {reg_basis_abs}"
        f" -reg_fn_abs {reg_fn_abs}"
        f" -reg_strength_abs {reg_strength_abs}"
        f" -out_coeffs {output_path}/sift2_coeffs.txt"
        f" -out_mu {output_path}/sift2_mu.txt"
        f" -differential {input_path}/fixels/fd/tp2_min_tp1_half.mif"
        f" {output_path}/sift2diff_weights.txt"
        f" -out_deltacoeffs {output_path}/sift2diff_coeffs.txt"
        f" -reg_basis_diff {reg_basis_diff}"
        f" -reg_strength_diff {reg_strength_diff}"
        f" -reg_fn_diff {reg_fn_diff}"
        f" -csv {output_path}/algorithm_convergence.csv"
        f" -streamline_groups {input_tcks_assignments}"
        f" {debug_option if debug else ''}"
        f" -min_iters {min_iters}"
        f" -force"
        ,log_path=f"{output_path}/sift2_log.txt")

    # summarise template + differences to connectomes   
    run_command(f"tck2connectome {input_tcks} {orig_path}/segmentations/gm_parcels.nii.gz {output_path}/connectome.csv -tck_weights_in {output_path}/sift2_weights.txt -symmetric -force")
    run_command(f"tck2connectome {input_tcks} {orig_path}/segmentations/gm_parcels.nii.gz {output_path}/connectome_diff_half.csv -tck_weights_in {output_path}/sift2diff_weights.txt -symmetric -force")
