import sys
import os

repository_path = "/Users/user/Downloads/sift2_unbiased/"
functions = os.path.join(repository_path, "code", "dependencies", "functions") 
sys.path.append(os.path.abspath(functions))

from run_command import run_command

tcksift2_cmd = "/Users/user/Documents/github/mrtrix3_sift2diff/bin/tcksift2"

def tcksift2_template(phantom_path,input_path,tcks,reg_basis_abs,reg_fn_abs,reg_strength_abs,debug=False):
        
        # Define Paths
        orig_path = os.path.join(phantom_path,"orig")
        
        ## SIFT2 template
        output_path = f"{input_path}/sift2_template/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/"
        os.makedirs(output_path, exist_ok=True)
        
        if debug:
            debug_tp_av = f"-output_debug {output_path}/debug"
            
        if tcks == "tracks_groundtruth":
            input_tcks = f"{phantom_path}/orig/ground_truth/tp1/tracks_gt_tp1.tck"
            input_tcks_assignments = f"{phantom_path}/orig/ground_truth/tp1/tracks_gt_tp1_assignments.txt"
        else:
            input_tcks = f"{input_path}/tp_average/{tcks}.tck"
            input_tcks_assignments = f"{input_path}/tp_average/{tcks}_assignments.txt"

        run_command(f"{tcksift2_cmd}"
            f" {input_tcks}"
            f" {input_path}/fixels/fd/tp1_tp2_mean.mif"
            f" {output_path}/sift2_weights.txt"
            f" -act {orig_path}/segmentations/5tt.mif*"
            f" -reg_basis_abs {reg_basis_abs}"
            f" -reg_strength_abs {reg_strength_abs}"
            f" -reg_fn_abs {reg_fn_abs}"
            f" -out_coeffs {output_path}/sift2_coeffs.txt"
            f" -out_mu {output_path}/sift2_mu.txt"
            f" -csv {output_path}/algorithm_convergence.csv"
            f" {debug_tp_av if debug else ''}"
            f" -streamline_groups {input_tcks_assignments}"
            f" -min_factor 0.00001"
            f" -info"
            f" -force"
            ,log_path=f"{output_path}/sift2_log.txt")
            
        run_command(f"tck2connectome {input_tcks} {orig_path}/segmentations/gm_parcels.nii.gz {output_path}/connectome.csv -tck_weights_in {output_path}/sift2_weights.txt -symmetric -force")
