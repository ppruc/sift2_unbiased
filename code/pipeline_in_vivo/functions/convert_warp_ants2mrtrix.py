import os
import sys
import shutil
import tempfile

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command

# Convert ANTs Warp
def convert_warp_ants2mrtrix(fixed, moving, warp_prefix, out_warp, ants_warp_marker=2147483647):
    
    # Create temporary directory
    tmp_dir = tempfile.mkdtemp()

    try:
        # Convert To MRTrix Format > Generate Identity Deformation Field
        run_command(f"warpinit {moving} {tmp_dir}/tmp_identity_warp[].nii -force", shell=True, check=True)
        
        # Convert To MRTrix Format > Transform Identity Warp
        for axis in (0, 1, 2):
            run_command(f"antsApplyTransforms"
                           f" -d 3"
                           f" -e 0"
                           f" -i {tmp_dir}/tmp_identity_warp{axis}.nii"
                           f" -o {tmp_dir}/tmp_mrtrix_warp{axis}.nii"
                           f" -r {fixed}"
                           f" -t {warp_prefix}1Warp.nii.gz"
                           f" -t {warp_prefix}0GenericAffine.mat"
                           f" --default-value {ants_warp_marker}"
                           , shell=True, check=True,
        )
        
        # Convert To MRTrix Format > Warpcorrect
        run_command(f"warpcorrect {tmp_dir}/tmp_mrtrix_warp[].nii {out_warp}"
                       f" -marker {ants_warp_marker} -force", shell=True, check=True
        )
        

    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir)