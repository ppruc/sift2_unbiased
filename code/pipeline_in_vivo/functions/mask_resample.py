import os
import shutil
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command

def mask_resample(mask_path_in, template_path_in, mask_path_out):

    try:
        shutil.rmtree("tmp_mask_resample")
    except:
        pass
    os.makedirs("tmp_mask_resample")
    
    run_command(f"voxel2mesh {mask_path_in} tmp_mask_resample/mesh.obj")
    run_command(f"meshfilter tmp_mask_resample/mesh.obj smooth tmp_mask_resample/mesh_smooth.obj")
    run_command(f"mesh2voxel tmp_mask_resample/mesh_smooth.obj {template_path_in} tmp_mask_resample/mask_resampled_partial.nii.gz")
    run_command(f"mrthreshold tmp_mask_resample/mask_resampled_partial.nii.gz {mask_path_out} -abs 0.5 -force")
    
    shutil.rmtree("tmp_mask_resample")
