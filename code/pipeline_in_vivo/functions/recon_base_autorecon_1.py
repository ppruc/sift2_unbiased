import os
import sys
import shutil

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def recon_base_autorecon_1(derivatives_dir,sub,remove_old_run=False):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    sessions = get_sessions(derivatives_dir,sub)
    ses1, ses2 = sessions
    print(f"ses1={ses1}, ses2={ses2}")

    # Remove old run in case of re-run
    if remove_old_run:
        try:
            shutil.rmtree(os.path.join(path, "ses-average", "fs_longitudinal"))
        except:
            print("no fs_longitudinal folder to remove - skipping")

    # Create Longitudinal Freesurfer Dir
    os.makedirs(os.path.join(path, "ses-average", "fs_longitudinal"), exist_ok=True)

    # Set subject directory
    os.environ["SUBJECTS_DIR"] = f"{path}/ses-average/fs_longitudinal/" # if run on server, otherwise set SUBJECTS_DIR =
   
    # Copy recon folder
    for ses in sessions:
        try:
            shutil.copytree(os.path.join(ses, 'anat', 'recon'), os.path.join('ses-average', 'fs_longitudinal', f'recon_{ses}'))
        except:
            print(f"{sub} recon_{ses} already exists; not copying")

    # Create longitudinal template
    run_command(f"recon-all"
                   + " " + " ".join(f"-tp {path}/ses-average/fs_longitudinal/recon_{ses}/" for ses in sessions)
                   + f" -base {path}/ses-average/fs_longitudinal/recon_template"
                   + f" -autorecon1"
                   )
