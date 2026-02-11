import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions
from modify_txt import modify_txt


cmd_tcksift2 = "/home/ppruckner/github/MRtrix3_sift2diff/bin/tcksift2" # needs to be installed
cmd_5ttregrid = "/home/ppruckner/github/mrtrix3_5ttregrid/bin/5ttregrid" # needs to be installed


def sift2_none(derivatives_dir,sub,ses,ntcks,fixel_metric,surgical=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    print(path)

    out_path = f"ses-average/weights/sift2_none/{ses}/"
    os.makedirs(os.path.join(out_path), exist_ok=True)
    
    if ses == ses1:
    
        # Regrid 5tt image to wmfod space
        run_command(f"{cmd_5ttregrid} {ses}/dwi/wmfod_norm.mif {ses}/dwi/5tt_regrid.mif -act {ses}/dwi/5tt.mif -force")
    
        # Run SIFT2
        run_command(f"{cmd_tcksift2}"
                    f" -act {ses}/dwi/5tt_regrid.mif"
                    f" {ses}/tcks/tracks_{ntcks}_session.tck"
                    f" {ses}/fixels/{fixel_metric}/{ses}.mif"
                    f" {out_path}/sift2_{ntcks}_weights.txt"
                    f" -reg_strength_abs 10000000000"
                    f" -max_iters 1"
                    f" -out_mu {out_path}/sift2_{ntcks}_mu.txt"
                    f" -csv {out_path}/algorithm_{ntcks}_convergence.txt"
                    f" -force"
                    )
    else:
        run_command(f"cp ses-average/weights/sift2_none/{ses1}/sift2_{ntcks}_mu.txt {out_path}/sift2_{ntcks}_mu.txt")
    
    if surgical:
        
        if ses == ses1:
        
            # Create a vector where all streamlines intersecting the resection are 1
            run_command(f"tcksample"
                        f" {ses}/tcks/tracks_{ntcks}_session.tck"
                        f" {ses}/surg_defect/surg_defect_final.nii.gz"
                        f" {ses}/tcks/tracks_{ntcks}_intersected_eq_1.txt"
                        f" -stat_tck max"
                        f" -nointerp"
                        f" -force"
                        )
                
            # Create a vector where all streamlines intersecting the resection are 0
            intersected_streamlines_eq_1  = np.loadtxt(f"{ses}/tcks/tracks_{ntcks}_intersected_eq_1.txt")
            switch_pairs = [(1,0),(0,1)]
            intersected_streamlines_eq_0 = modify_txt(intersected_streamlines_eq_1, switch_pairs)
            np.savetxt(f"{ses}/tcks/tracks_{ntcks}_intersected_eq_0.txt",
                       intersected_streamlines_eq_0,
                       fmt='%.0f',
                       delimiter=" ",
                       header="modified streamline vector - all streamlines intersecting the resection cavity are set to 0"
                       )
                        
            # set all preoperative weights that intersect the resection cavity to zero (restricting the analysis to non-resected connections)
            sift2_weights_intersected_eq_0 = np.loadtxt(f"{out_path}/sift2_{ntcks}_weights.txt") * intersected_streamlines_eq_0
            np.savetxt(f"{out_path}/sift2_{ntcks}_weights_intersected_eq_0.txt",
                       sift2_weights_intersected_eq_0,
                       delimiter=" ",
                       header="modified streamline vector - all streamlines intersecting the resection cavity are set to 0"
                       )

    if surgical and ses == ses1:
        run_command(f"tck2connectome"
                    f" {ses}/tcks/tracks_{ntcks}_session.tck"
                    f" {ses}/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
                    f" {out_path}/connectome_{ntcks}.csv"
                    f" -tck_weights_in {out_path}/sift2_{ntcks}_weights_intersected_eq_0.txt"
                    f" -symmetric"
                    f" -force"
                    )
         
    else:
        run_command(f"tck2connectome"
                    f" {ses}/tcks/tracks_{ntcks}_session.tck"
                    f" {ses}/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
                    f" {out_path}/connectome_{ntcks}.csv"
                    f" -symmetric"
                    f" -force"
                    )
        
    connectome = pd.read_csv(f"{out_path}/connectome_{ntcks}.csv", header=None) * np.loadtxt(f"{out_path}/sift2_{ntcks}_mu.txt")
    connectome.to_csv(f"{out_path}/connectome_{ntcks}_fbc.csv", header=False, index=False)
