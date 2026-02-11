import os
import sys
import shutil
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions
from modify_txt import modify_txt

cmd_tcksift2 = "/path/to/mrtrix3_sift2diff/bin/tcksift2" # needs to be installed


def sift2_symmetric(derivatives_dir,sub,ses,ntcks,fixel_metric,reg_basis_temp=None,reg_fn_temp=None,reg_strength_temp=None,reg_basis_init=None,reg_fn_init=None,reg_strength_init=None,surgical=False,skip_sift2=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    print(path)
    
    out_path = f"ses-average/weights/sift2_symmetric/{ses}/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/reg_basis_init_{reg_basis_init}/reg_fn_init_{reg_fn_init}/reg_strength_init_{reg_strength_init}"
    os.makedirs(os.path.join(out_path), exist_ok=True)

    init_factors_path = f"ses-average/weights/sift2_template/ses-average/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/sift2_{ntcks}_weights.txt"
    in_mu = np.loadtxt(f"ses-average/weights/sift2_template/ses-average/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/sift2_{ntcks}_mu.txt")
    
    if surgical:
                    
        # Define input and output paths
        intersected_streamlines_eq_1 = np.loadtxt(f"ses-average/tcks/tracks_{ntcks}_intersected_eq_1.txt")
        intersected_streamlines_eq_0_path = f"ses-average/tcks/tracks_{ntcks}_intersected_eq_0.txt"
                 
        # Create vector were all streamlines intersecting the resection are 0 
        switch_pairs = [(1,0),(0,1)]
        intersected_streamlines_eq_0 = modify_txt(intersected_streamlines_eq_1, switch_pairs)
        np.savetxt(intersected_streamlines_eq_0_path,
                intersected_streamlines_eq_0,
                fmt='%.0f',
                delimiter=" ",
                header="modified streamline vector - all streamlines intersecting the resection cavity are set to 0"
                )
        
        # load average sift2 weights
        init_factors = np.loadtxt(init_factors_path)
        
        # set interesecting streamlines to zero
        init_factors_modified = init_factors * intersected_streamlines_eq_0
        
        # save modified weights
        init_factors_modified_path = f"ses-average/weights/sift2_template/ses-average/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/sift2_{ntcks}_weights_intersected_streamlines_eq_0.txt"

        np.savetxt(init_factors_modified_path,
                init_factors_modified,
                delimiter=" ",
                header="modified sift2 weights - all streamlines intersecting the resection cavity are set to 0"
                )
    
    if not surgical:
        init_template = f" -init_factors {init_factors_path}"
    else:
        if ses == ses1:
            init_template = f" -init_factors {init_factors_path}"
        elif ses == ses2:
            init_template = f" -init_factors {init_factors_modified_path}"
        else:
            raise ValueError("ses must be either ses1 or ses2")


    if not skip_sift2:
        run_command(f"{cmd_tcksift2}"
                f" -act ses-average/wmfod_template/5tt_regrid.mif"
                f" ses-average/tcks/tracks_{ntcks}_template.tck"
                f" ses-average/fixels/{fixel_metric}/{ses}.mif"
                f" {out_path}/sift2_{ntcks}_weights.txt"
                f" -in_mu {in_mu}"
                f" {init_template}"
                f" -streamline_groups ses-average/tcks/tracks_{ntcks}_template_assignments.txt"
                f" -reg_basis_abs {reg_basis_init}"
                f" -reg_fn_abs {reg_fn_init}"
                f" -reg_strength_abs {reg_strength_init}"
                f" -out_mu {out_path}/sift2_{ntcks}_mu.txt"
                f" -out_coeffs {out_path}/sift2_{ntcks}_coeffs.txt"
                f" -csv {out_path}/algorithm_{ntcks}_convergence.txt"
                f" -force"
                )
        
    if surgical:
    
        # ensures that streamlines intersecting the resection are zero (already the case in postop, setting also for preop to restrict analysis to non-resected connections)
        sift2_weights_modified = np.loadtxt(f'{out_path}/sift2_{ntcks}_weights.txt') * intersected_streamlines_eq_0
        np.savetxt(f'{out_path}/sift2_{ntcks}_weights_intersected_eq_0.txt',
                sift2_weights_modified,
                delimiter=" ",
                header="modified streamline vector - all streamlines intersecting the resection cavity are set to 0"
                )

    run_command(f"tck2connectome"
        f" ses-average/tcks/tracks_{ntcks}_template.tck"
        f" ses-average/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
        f" {out_path}/connectome_{ntcks}.csv"
        f" -tck_weights_in {out_path}/sift2_{ntcks}_weights{'_intersected_eq_0' if surgical else ''}.txt"
        f" -symmetric"
        f" -force"
        )
    
    connectome = pd.read_csv(f"{out_path}/connectome_{ntcks}.csv", header=None) * np.loadtxt(f"{out_path}/sift2_{ntcks}_mu.txt")
    connectome.to_csv(f"{out_path}/connectome_{ntcks}_fbc.csv", header=False, index=False)

