import os
import sys
import numpy as np
import pandas as pd


sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions
from modify_txt import modify_txt

cmd_tcksift2 = "/path/to/mrtrix3_sift2diff/bin/tcksift2" # needs to be installed
cmd_5ttregrid = "/path/to/mrtrix3_5ttregrid/bin/5ttregrid" # needs to be installed
    
def sift2_differential(derivatives_dir,sub,ntcks,fixel_metric,reg_basis_temp=None,reg_fn_temp=None,reg_strength_temp=None,reg_basis_diff=None,reg_fn_diff=None,reg_strength_diff=None,surgical=False,skip_sift2=False):
        
    print(f"processing {sub}")
    print(f"running sift2diff")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    print(path)
    
    # Create output dirs
    out_path = f"ses-average/weights/sift2_differential/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/reg_basis_diff_{reg_basis_diff}/reg_fn_diff_{reg_fn_diff}/reg_strength_diff_{reg_strength_diff}"
    
    os.makedirs(os.path.join(out_path), exist_ok=True)
    
    #Input files
    in_mu = np.loadtxt(f"ses-average/weights/sift2_template/ses-average/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/sift2_{ntcks}_mu.txt")
    in_factors = f"ses-average/weights/sift2_template/ses-average/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/sift2_{ntcks}_weights.txt"

    if surgical:
        
        # Define input and output paths
        intersected_streamlines_eq_1 = np.loadtxt(f"ses-average/tcks/tracks_{ntcks}_intersected_eq_1.txt")
        init_deltacoeffs_path = f"ses-average/tcks/tracks_{ntcks}_intersected_eq_-1.txt"
        mask_differential_path = f"ses-average/tcks/tracks_{ntcks}_intersected_eq_0.txt"
        
        # Create init_deltacoeffs
        switch_pairs = [(1,-1)]
        init_deltacoeffs = modify_txt(intersected_streamlines_eq_1, switch_pairs)
        np.savetxt(init_deltacoeffs_path,
                   init_deltacoeffs,
                   fmt='%.0f',
                   delimiter=" ",
                   header="modified streamline vector - all streamlines intersecting the resection cavity are set to -1"
                   )
        
        # Create mask_differential
        switch_pairs = [(1,0),(0,1)]
        mask_differential = modify_txt(intersected_streamlines_eq_1, switch_pairs)
        np.savetxt(mask_differential_path,
                   mask_differential,
                   fmt='%.0f',
                   delimiter=" ",
                   header="modified streamline vector - all streamlines intersecting the resection cavity are set to 0"
                   )
                
        init_deltacoeffs_option = f" -init_deltacoeffs {init_deltacoeffs_path}"
        mask_differential_option = f" -mask_differential {mask_differential_path}"

        
    if not skip_sift2:
        run_command(f"{cmd_tcksift2}"
            f" -act ses-average/wmfod_template/5tt_regrid.mif"
            f" ses-average/tcks/tracks_{ntcks}_template.tck"
            f" ses-average/fixels/{fixel_metric}/{ses1}_{ses2}_mean.mif"
            f" {out_path}/sift2_{ntcks}_weights.txt"
            f" -streamline_groups ses-average/tcks/tracks_{ntcks}_template_assignments.txt"
            f" -in_factors {in_factors}"
            f" -in_mu {in_mu}"
            f" -differential ses-average/fixels/{fixel_metric}/{ses2}_min_{ses1}_half.mif"
            f" {out_path}/sift2diff_weights.txt"
            f" -reg_basis_diff {reg_basis_diff}"
            f" -reg_fn_diff {reg_fn_diff}"
            f" -reg_strength_diff {reg_strength_diff}"
            f" -max_deltacoeff_step 0.09"
            f" -out_deltacoeffs {out_path}/sift2diff_coeffs.txt"
            f" -out_mu {out_path}/sift2_{ntcks}_mu.txt"
            f" -out_coeffs {out_path}/sift2_{ntcks}_coeffs.txt"
            f" -csv {out_path}/algorithm_{ntcks}_convergence.txt"
            f"{init_deltacoeffs_option if surgical else ''}"
            f"{mask_differential_option if surgical else ''}"
            f" -force"
            )

    if surgical:
    
        # ensures that differential weights of streamlines intersecting the resection are zero (to restrict analysis to non-resected connections)
        intersected_streamlines_eq_0 = np.loadtxt(f'ses-average/tcks/tracks_{ntcks}_intersected_eq_0.txt')
        sift2diff_weights_modified = np.loadtxt(f'{out_path}/sift2diff_weights.txt') * intersected_streamlines_eq_0
        np.savetxt(f'{out_path}/sift2diff_weights_intersected_eq_0.txt',
                sift2diff_weights_modified,
                delimiter=" ",
                header="modified streamline vector - all streamlines intersecting the resection cavity are set to 0"
                )
    
    run_command(f"tck2connectome"
        f" ses-average/tcks/tracks_{ntcks}_template.tck"
        f" ses-average/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
        f" {out_path}/connectome_{ntcks}_template.csv"
        f" -tck_weights_in {out_path}/sift2_{ntcks}_weights.txt"
        f" -symmetric"
        f" -force"
        )
        
    run_command(f"tck2connectome"
        f" ses-average/tcks/tracks_{ntcks}_template.tck"
        f" ses-average/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
        f" {out_path}/connectome_{ntcks}_diff_half.csv"
        f" -tck_weights_in {out_path}/sift2diff_weights{'_intersected_eq_0' if surgical else ''}.txt"
        f" -symmetric"
        f" -force"
        )
    
    connectome_temp = pd.read_csv(f"{out_path}/connectome_{ntcks}_template.csv", header=None) * np.loadtxt(f"{out_path}/sift2_{ntcks}_mu.txt")
    connectome_temp.to_csv(f"{out_path}/connectome_{ntcks}_template_fbc.csv", header=False, index=False)

    connectome_diff_half = pd.read_csv(f"{out_path}/connectome_{ntcks}_diff_half.csv", header=None) * np.loadtxt(f"{out_path}/sift2_{ntcks}_mu.txt")
    connectome_diff_half.to_csv(f"{out_path}/connectome_{ntcks}_diff_half_fbc.csv", header=False, index=False)

    connectome_tp1 = connectome_temp - connectome_diff_half
    connectome_tp2 = connectome_temp + connectome_diff_half
    connectome_tp1.to_csv(f"{out_path}/connectome_{ntcks}_tp1_fbc.csv", header=False, index=False)
    connectome_tp2.to_csv(f"{out_path}/connectome_{ntcks}_tp2_fbc.csv", header=False, index=False)

    connectome_diff = connectome_diff_half * 2
    connectome_diff.to_csv(f"{out_path}/connectome_{ntcks}_diff_full_fbc.csv", header=False, index=False)
