import sys
import os

repository_path = "/Users/user/Downloads/sift2_unbiased/"
functions = os.path.join(repository_path, "code", "dependencies", "functions") 
sys.path.append(os.path.abspath(functions))

from run_command import run_command
tcksift2_cmd = "/Users/user/Documents/github/mrtrix3_sift2diff/bin/tcksift2"

def tcksift2_none(phantom_path, input_path, tcks, tp):
        
        # Define Paths
        orig_path = os.path.join(phantom_path,"orig")
        
        ## SIFT2 template
        output_path = f"{input_path}/sift2_none/{tcks}/"
        os.makedirs(output_path, exist_ok=True)
            
        input_tcks = f"{input_path}/{tp}/{tcks}.tck"

        # Run SIFT2 without optimisation to derive the value mu    
        run_command(f"{tcksift2_cmd}"
            f" {input_tcks}"
            f" {input_path}/fixels/fd/{tp}.mif"
            f" {output_path}/sift2_weights_{tp}.txt"
            f" -act {orig_path}/segmentations/5tt.mif*"
            f" -reg_strength_abs 100000000000000" # overregularisation so optimiser does not converge
            f" -out_mu {output_path}/sift2_mu_{tp}.txt"
            f" -csv {output_path}/algorithm_convergence.csv"
            f" -force"
            )

        # Sum to connectome
        run_command(f"tck2connectome"
            f" {input_tcks}"
            f" {orig_path}/segmentations/gm_parcels.nii.gz"
            f" {output_path}/connectome_{tp}.csv"
            f" -out_assignments {output_path}/connectome_{tp}_assignments.txt"
            f" -symmetric"
            f" -force"
            )
