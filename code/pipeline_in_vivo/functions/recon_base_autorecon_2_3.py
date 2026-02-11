import os
import sys
import shutil

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def recon_base_autorecon_2_3(derivatives_dir,sub,inject_template=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")
    
    if inject_template:
    
        run_command(f"mrconvert"
            f" ses-average/fs_longitudinal/recon_template/mri/norm_template.mgz"
            f" ses-average/fs_longitudinal/recon_template/mri/norm_template_unrefined.mgz"
            )
            
        # Replace rigid freesurfer template with nonlinear ants template
        if os.path.exists("ses-average/template/t1w_template_corr.nii.gz"):
            input = "ses-average/template/t1w_template_corr.nii.gz"
        else:
            input = "ses-average/template/t1w_template.nii.gz"
        
        run_command(f"mri_vol2vol"
                    f" --mov {input}"
                    f" --targ ses-average/fs_longitudinal/recon_template/mri/norm_template_unrefined.mgz"
                    f" --o ses-average/fs_longitudinal/recon_template/mri/norm_template.mgz"
                    f" --interp cubic"
                    f" --regheader"
                    )

    # Set subject directory
    os.environ["SUBJECTS_DIR"] = f"{path}/ses-average/fs_longitudinal/"
    
    try:
        run_command(f"rm /data/data_Philip/TEMP_TRACTS/BIDS/derivatives/{sub}/ses-average/fs_longitudinal/recon_template/scripts/IsRunning.lh+rh")
    except:
        pass

    # Proceed with base template reconstruction
    run_command(f"recon-all"
                   + " " + " ".join(f"-tp {path}/ses-average/fs_longitudinal/recon_{ses}/" for ses in sessions)
                   + f" -base {path}/ses-average/fs_longitudinal/recon_template"
                   + f" -autorecon2 -autorecon3 -careg"
                   )
