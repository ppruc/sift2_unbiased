import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from convert_tck_label_to_number import convert_tck_label_to_number


def tck_session(derivatives_dir,sub,ses,ntcks_str,surgical=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)
    
    ntcks = convert_tck_label_to_number(ntcks_str)

    print(f"generating {ntcks_str}")

    # Create output dirs
    os.makedirs(os.path.join(path, ses, "tcks"), exist_ok=True)
    
    # Create 5tt image
    run_command(f"5ttgen"
            f" hsvs {ses}/anat/recon/"
            f" {ses}/dwi/5tt.mif"
            f" -template {ses}/dwi/mask_upsampled.nii.gz"
            f" -force"
            )

    # Perform fiber tracking in template space
    run_command(f"tckgen {ses}/dwi/wmfod_norm.mif"
                    f" {ses}/tcks/tracks_{ntcks_str}_session.tck"
                    f" -act {ses}/dwi/5tt.mif"
                    f" -backtrack"
                    f" -seed_dynamic {ses}/dwi/wmfod_norm.mif"
                    f" -select {ntcks}"
                    f" -force"
                    )

    # Select a subset of the streamlines for viewing
    run_command(f"tckedit"
                    f" {ses}/tcks/tracks_{ntcks_str}_session.tck"
                    f" {ses}/tcks/tracks_100k_session.tck"
                    f" -number 100000"
                    f" -force"
                    )
                    
    # Create streamline assignments
    run_command(f"tck2connectome"
        f" {ses}/tcks/tracks_{ntcks_str}_session.tck"
        f" {ses}/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
        f" {ses}/tcks/tmp_connectome.csv"
        f" -out_assignments {ses}/tcks/tracks_{ntcks_str}_session_assignments.txt"
        f" -symmetric"
        f" -force"
        )
    
    run_command(f"{ses}/tcks/tmp_connectome.csv")
    
               

    

        
