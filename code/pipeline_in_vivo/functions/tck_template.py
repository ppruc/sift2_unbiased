import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions
from convert_tck_label_to_number import convert_tck_label_to_number

def tck_template(derivatives_dir,sub,ntcks_str,surgical=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    
    ntcks = convert_tck_label_to_number(ntcks_str)
        
    print(f"generating {ntcks_str}")

    # Create output dirs
    os.makedirs(os.path.join(path, "ses-average", "tcks"), exist_ok=True)
    
    # Create 5tt image
    run_command(f"5ttgen"
            f" hsvs ses-average/fs_longitudinal/recon_template/"
            f" ses-average/wmfod_template/5tt.mif"
            f" -template ses-average/wmfod_template/wmfod_template_mask.mif"
            f" -force"
            )

    # Perform fiber tracking in template space
    run_command(f"tckgen ses-average/wmfod_template/wmfod_template.mif"
                    f" ses-average/tcks/tracks_{ntcks_str}_template.tck"
                    f" -act ses-average/wmfod_template/5tt.mif"
                    f" -backtrack"
                    f" -seed_dynamic ses-average/wmfod_template/wmfod_template.mif"
                    f" -select {ntcks}"
                    f" -force"
                    )

    # Select a subset of the streamlines for viewing
    run_command(f"tckedit"
                    f" ses-average/tcks/tracks_{ntcks_str}_template.tck"
                    f" ses-average/tcks/tracks_100k_template.tck"
                    f" -number 100000"
                    f" -force"
                    )
                    
    # Create streamline assignments
    run_command(f"tck2connectome"
        f" ses-average/tcks/tracks_{ntcks_str}_template.tck"
        f" ses-average/atlases/{'ipsi_contra/' if surgical else ''}Desikan-Killiany{'_ipsi_contra' if surgical else ''}.nii.gz"
        f" ses-average/tcks/tmp_connectome.csv"
        f" -out_assignments ses-average/tcks/tracks_{ntcks_str}_template_assignments.txt"
        f" -symmetric"
        f" -force"
        )
    
    run_command(f"rm ses-average/tcks/tmp_connectome.csv")
               

    

        
