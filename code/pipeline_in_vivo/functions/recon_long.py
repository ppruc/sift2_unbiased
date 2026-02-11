import os
import sys
import shutil

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command

def recon_long(derivatives_dir,sub,ses):
        
    print(f"processing {sub}")
    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)

    # Set subject directory
    os.environ["SUBJECTS_DIR"] = f"{path}/ses-average/fs_longitudinal/"

    run_command(f"recon-all -long {path}/ses-average/fs_longitudinal/recon_{ses} {path}/ses-average/fs_longitudinal/recon_template -all")
