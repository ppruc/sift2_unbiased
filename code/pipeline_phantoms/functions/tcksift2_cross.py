import sys
import os
import shutil

repository_path = "/Users/user/Downloads/sift2_unbiased/"
functions = os.path.join(repository_path, "code", "dependencies", "functions") 
sys.path.append(os.path.abspath(functions))

from run_command import run_command
tcksift2_cmd = "/Users/user/Documents/github/mrtrix3_sift2diff/bin/tcksift2"

def tcksift2_cross(phantom_path, input_path, tcks, tp,reg_basis_abs, reg_fn_abs, reg_strength_abs,fixel_correspondence=False, debug=False, min_factor=False):
        """
        Run cross-sectional SIFT2 optimisation on a tractogram for a given phantom timepoint and generate weighted connectomes.

        Parameters
        ----------
        phantom_path : str
            Path to the phantom root directory containing the `orig` data, including
            segmentations and reconstructed tractograms.
        input_path : str
            Path to the directory containing reconstructed tractograms, fixels, and
            derived data for each timepoint.
        tcks : str
            Name of the tractogram to process (e.g. reconstructed tractogram name).
        tp : str
            Timepoint identifier (e.g. `"tp1"` or `"tp2"`).
        reg_basis_abs : str
            basis used for absolute SIFT2 regularisation.
        reg_fn_abs : str
            basis function used for absolute SIFT2 regularisation.
        reg_strength_abs : float
            Regularisation strength for absolute SIFT2 optimisation.
        fixel_correspondence : bool, optional
            If True, use fixel images with enforced correspondence across timepoints;
            otherwise use timepoint-specific fixel directories (default: False).
        debug : bool, optional
            If True, enable SIFT2 debug output and write additional diagnostic files
            (default: False).

        Outputs
        -------
        - Streamline weights (`sift2_weights_<tp>.txt`)
        - Absolute SIFT2 coefficients and mu parameters
        - Convergence diagnostics (CSV)
        - Weighted symmetric connectome (CSV)
        - Streamline-to-node assignments

        Notes
        -----
        - Uses a 5TT image for ACT-based filtering.
        - Requires MRtrix3 with SIFT2absolute support.
        """
        
        # Define Paths
        orig_path = os.path.join(phantom_path,"orig")
        output_path = f"{input_path}/sift2_cross/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/"
        os.makedirs(output_path, exist_ok=True)
        
        if debug:
            debug_path = f"-output_debug {output_path}/debug_{tp}"
            
        input_tcks = f"{input_path}/{tp}/{tcks}.tck"
        input_tcks_assignments = f"{input_path}/{tp}/{tcks}_assignments.txt"
            
        if fixel_correspondence:
            fixels = f"{input_path}/fixels/fd/{tp}.mif"
        else:
            fixels = f"{input_path}/fixels/{tp}/fd.mif"

        # at small regularisation weights sift2 can produce weights so small that tck2connectome fails; setting to True constrains the minimum weight; however unconstrained weights necessary for reliable Lcurve analysis
        if min_factor:
             min_factor = f" -min_factor 1.0e-6"
        else:
            min_factor = ""

        # run SIFT2 cross-sectional
        run_command(f"{tcksift2_cmd}"
            f" {input_tcks}"
            f" {fixels}"
            f" {output_path}/sift2_weights_{tp}.txt"
            f" -act {orig_path}/segmentations/5tt.mif*"
            f" -reg_basis_abs {reg_basis_abs}"
            f" -reg_fn_abs {reg_fn_abs}"
            f" -reg_strength_abs {reg_strength_abs}"
            f" -out_coeffs {output_path}/sift2_coeffs_{tp}.txt"
            f" -out_mu {output_path}/sift2_mu_{tp}.txt"
            f" -csv {output_path}/algorithm_convergence_{tp}.csv"
            f" -streamline_group {input_tcks_assignments}"
            f" {min_factor}"
            f" {debug_path if debug else ''}"
            f" -info"
            f" -force"
            ,log_path=f"{output_path}/sift2_log_{tp}.txt")

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
