import os
import sys
import shutil

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

cmd_tcksift2 = "/path/to/mrtrix3_sift2diff/bin/tcksift2" # needs to be installed 
cmd_5ttregrid = "/path/to/mrtrix3_5ttregrid/bin/5ttregrid" # needs to be installed


def sift2_template(derivatives_dir,sub,ntcks,fixel_metric,reg_basis_temp=None,reg_fn_temp=None,reg_strength_temp=None,surgical=False,skip_sift2=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    print(path)

    # Create output dirs
    out_path = f"ses-average/weights/sift2_template/ses-average/{fixel_metric}/reg_basis_temp_{reg_basis_temp}/reg_fn_temp_{reg_fn_temp}/reg_strength_temp_{reg_strength_temp}/"
    os.makedirs(os.path.join(out_path), exist_ok=True)
    
    if surgical:
        
        # Modify SIFT2 weights by setting streamlines that intersect the resection zone to zero
        run_command(f"tcksample"
            f" ses-average/tcks/tracks_{ntcks}_template.tck"
            f" ses-average/surg_defect/surg_defect_final.nii.gz"
            f" ses-average/tcks/tracks_{ntcks}_intersected_eq_1.txt"
            f" -stat_tck max"
            f" -nointerp"
            f" -force"
            )
    
    run_command(f"{cmd_5ttregrid} ses-average/wmfod_template/wmfod_template.mif ses-average/wmfod_template/5tt_regrid.mif -act ses-average/wmfod_template/5tt.mif -force")
    
    run_command(f"tck2connectome"
        f" ses-average/tcks/tracks_{ntcks}_template.tck"
        f" ses-average/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
        f" {out_path}/tmp_connectome.csv"
        f" -out_assignments ses-average/tcks/tracks_{ntcks}_template_assignments.txt"
        f" -symmetric"
        f" -force"
        )
        
    run_command(f"rm {out_path}/tmp_connectome.csv")
    
    if not skip_sift2:
        run_command(f"{cmd_tcksift2}"
                f" -act ses-average/wmfod_template/5tt_regrid.mif"
                f" ses-average/tcks/tracks_{ntcks}_template.tck"
                f" ses-average/fixels/{fixel_metric}/{ses1}_{ses2}_mean.mif"
                f" {out_path}/sift2_{ntcks}_weights.txt"
                f" -streamline_groups ses-average/tcks/tracks_{ntcks}_template_assignments.txt"
                f" -reg_basis_abs {reg_basis_temp}"
                f" -reg_fn_abs {reg_fn_temp}"
                f" -reg_strength_abs {reg_strength_temp}"
                f" -out_mu {out_path}/sift2_{ntcks}_mu.txt"
                f" -out_coeffs {out_path}/sift2_{ntcks}_coeffs.txt"
                f" -csv {out_path}/algorithm_{ntcks}_convergence.txt"
                f" -force",
                log_path=f"{out_path}/sift2_{ntcks}_log.txt"
                )
        
    run_command(f"tck2connectome"
        f" ses-average/tcks/tracks_{ntcks}_template.tck"
        f" ses-average/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
        f" {out_path}/connectome_{ntcks}.csv"
        f" -tck_weights_in {out_path}/sift2_{ntcks}_weights.txt"
        f" -out_assignments ses-average/tcks/tracks_{ntcks}_assignments.txt"
        f" -symmetric"
        f" -force"
        )
        
