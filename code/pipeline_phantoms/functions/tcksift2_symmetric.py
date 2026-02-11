import sys
import os
import numpy as np

repository_path = "/Users/user/Downloads/sift2_unbiased/"
functions = os.path.join(repository_path, "code", "dependencies", "functions") 
sys.path.append(os.path.abspath(functions))

from run_command import run_command
tcksift2_cmd = "/Users/user/Documents/github/mrtrix3_sift2diff/bin/tcksift2"

def tcksift2_symmetric(phantom_path, input_path, tcks, tp, reg_basis_abs_init, reg_fn_abs_init, reg_strength_abs_init, reg_basis_abs, reg_fn_abs, reg_strength_abs, fixel_correspondence=True, debug=False):
    """
    Perform symmetric SIFT2 optimisation on unbiased tractograms.

    Parameters
    ----------
    phantom_path : str
        Path to the phantom data directory.
    input_path : str
        Path where input files and templates are stored.
    tcks : str
        Name of the tractogram to process.
    tp : str
        Timepoint identifier.
    reg_basis_abs_init : str
        the regularisation basis that was used for optimisation of the unbiased tractogram 
    reg_strength_abs_init : float
        the regularisation strength that was used for optimisation of the unbiased tractogram 
    reg_basis_abs : str
        the regularisation basis to be used for further optimisation of the unbiased tractogram 
    reg_strength_abs : float
        the regularisation strength to be used for further optimisation of the unbiased tractogram 
    fixel_correspondence : bool, optional
        Whether fixel correspondence is used for input fixel images (default is True).
    debug : bool, optional
        Whether to output debug information (default is False).

    Outputs
    -------
    - SIFT2 weights file
    - SIFT2 coefficients file
    - SIFT2 mu file
    - Algorithm convergence CSV file
    - Symmetric connectome CSV and assignments

    """
        
    # Define Paths
    orig_path = os.path.join(phantom_path,"orig")
    
    ## SIFT2 template
    init_weights = f" -init_factors {input_path}/sift2_template/{tcks}/reg_basis_abs_{reg_basis_abs_init}/reg_fn_abs_{reg_fn_abs_init}/reg_abs_{reg_strength_abs_init}/sift2_weights.txt"
    in_mu_path = np.loadtxt(f"{input_path}/sift2_template/{tcks}/reg_basis_abs_{reg_basis_abs_init}/reg_fn_abs_{reg_fn_abs_init}/reg_abs_{reg_strength_abs_init}/sift2_mu.txt")
    in_mu = f" -in_mu {in_mu_path}"
    output_path = f"{input_path}/sift2_symmetric/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/"
    os.makedirs(output_path, exist_ok=True)
    
    if debug:
        debug = f"-output_debug {output_path}/debug_{tp}"
        
    input_tcks = f"{input_path}/tp_average/{tcks}.tck"
    input_tcks_assignments = f"{input_path}/tp_average/{tcks}_assignments.txt"
                   
    if fixel_correspondence:
        input_fixels = f" {input_path}/fixels/fd/{tp}.mif"
    else:
        input_fixels = f" {input_path}/fixels/{tp}/fd.mif"

    # Run SIFT2 with initialised weights
    run_command(f"{tcksift2_cmd}"
        f" {input_tcks}"
        f" {input_fixels}"
        f" {output_path}/sift2_weights_{tp}.txt"
        f" {in_mu}"
        f" {init_weights}"
        f" -streamline_groups {input_tcks_assignments}"
        f" -act {orig_path}/segmentations/5tt.mif*"
        f" -reg_basis_abs {reg_basis_abs}"
        f" -reg_strength_abs {reg_strength_abs}"
        f" -out_coeffs {output_path}/sift2_coeffs_{tp}.txt"
        f" -out_mu {output_path}/sift2_mu_{tp}.txt"
        f" -csv {output_path}/algorithm_convergence_{tp}.csv"
        f" {debug if debug else ''}"
        f" -info"
        f" -force"
        ,log_path=f"{output_path}/sift2_log.txt")

    # Sum to connectome    
    run_command(f"tck2connectome"
        f" {input_tcks}"
        f" {orig_path}/segmentations/gm_parcels.nii.gz"
        f" {output_path}/connectome_{tp}.csv"
        f" -tck_weights_in {output_path}/sift2_weights_{tp}.txt"
        f" -out_assignments {output_path}/connectome_{tp}_assignments.txt"
        f" -symmetric"
        f" -force"
        )
