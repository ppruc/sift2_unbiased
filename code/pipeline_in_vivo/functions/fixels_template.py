import os
import sys

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

cmd_fixelcorrespondence = '/path/to//mrtrix3_fixelcorrespondence/bin/fixelcorrespondence' # updated fixelcorrespondence command needs to be installed
cmd_fixel2fixel = '/path/to/mrtrix3_fixelcorrespondence/bin/fixel2fixel' # updated fixelcorrespondence command needs to be installed

def fixels_template(derivatives_dir,sub,registration):

    path = os.path.join(derivatives_dir, sub)
    os.chdir(path)
    
    # Create wmfod not reoriented dir
    os.makedirs(f"ses-average/wmfod_template/wmfod_TRANSFORMED", exist_ok=True)
    
    sessions = get_sessions(derivatives_dir, sub)
    ses1, ses2 = sessions
    
    for ses in sessions:

        # Transform wmfod data without FOD reorientation
        run_command(f"mrtransform {ses}/dwi/wmfod_norm.mif"
            f" ses-average/wmfod_template/wmfod_TRANSFORMED/{ses}.mif"
            f" {'-linear' if registration == 'rigid' else '-warp'}"
            f" ses-average/transforms/{ses}/sub2temp_{'rigid.txt' if registration == 'rigid' else 'wmfod_deformation.mif'}"
            f" -reorient_fod {'yes' if registration == 'rigid' else 'no'}"
            f" -template ses-average/wmfod_template/wmfod_template.mif"
            f" -force"
            )
        
    run_command(f"rm -r ses-average/fixels/")
    run_command(f"mkdir -p ses-average/fixels/fd")
    
    run_command(f"fod2fixel"
        f" -mask ses-average/wmfod_template/wmfod_template_mask.mif"
        f" -fmls_peak_value 0.06"
        f" ses-average/wmfod_template/wmfod_template.mif"
        f" ses-average/fixels/fixel_mask"
        f" -afd fd.mif"
        f" -maxnum 4"
        f" -force"
        )
    
    for ses in sessions:
        
        run_command(f"fod2fixel"
            f" ses-average/wmfod_template/wmfod_TRANSFORMED/{ses}.mif"
            f" -mask ses-average/wmfod_template/wmfod_template_mask.mif"
            f" ses-average/fixels/{ses}_TRANSFORMED"
            f" -afd fd.mif"
            f" -maxnum 4"
            f" -force"
            )
            
        if registration != 'rigid':
            
            run_command(f"fixelreorient"
                f" ses-average/fixels/{ses}_TRANSFORMED"
                f" ses-average/transforms/{ses}/sub2temp_{'rigid.txt' if registration == 'rigid' else 'wmfod_deformation.mif'}"
                f" ses-average/fixels/{ses}"
                f" -force"
                )
            run_command(f"rm -r ses-average/fixels/{ses}_TRANSFORMED")
    
        else:
            run_command(f"mv ses-average/fixels/{ses}_TRANSFORMED ses-average/fixels/{ses}")


    run_command(f"rm -r ses-average/wmfod_template/wmfod_TRANSFORMED")

    run_command(f"cp ses-average/fixels/fixel_mask/index.mif ses-average/fixels/fixel_mask/directions.mif ses-average/fixels/fd/")
    
    if registration != 'rigid':
    
        for folder in ("fc", "log_fc", "fdc"):
        
            run_command(f"rm -r ses-average/fixels/{folder}")
            run_command(f"mkdir ses-average/fixels/{folder}")
            run_command(f"cp ses-average/fixels/fd/index.mif ses-average/fixels/fd/directions.mif ses-average/fixels/{folder}")
    
    for ses in sessions:
    
        run_command(f"{cmd_fixelcorrespondence}"
            f" ses-average/fixels/{ses}/fd.mif"
            f" ses-average/fixels/fixel_mask/fd.mif"
            f" ses-average/fixels/fixel_mask/{ses}_to_template"
            f" -algorithm in2023"
            f" -force"
            )
            
        run_command(f"{cmd_fixel2fixel}"
            f" ses-average/fixels/{ses}/fd.mif"
            f" ses-average/fixels/fixel_mask/{ses}_to_template"
            f" sum ses-average/fixels/fd/"
            f" {ses}.mif"
            f" -force"
            )
            
        if registration != 'rigid':
            
            run_command(f"warp2metric"
                f" ses-average/transforms/{ses}/sub2temp_wmfod_deformation.mif"
                f" -fc ses-average/fixels/fd/"
                f" ses-average/fixels/fc"
                f" {ses}.mif"
                )
                
            run_command(f"mrcalc ses-average/fixels/fc/{ses}.mif -log ses-average/fixels/log_fc/{ses}.mif -force")
            
            run_command(f"mrcalc ses-average/fixels/fd/{ses}.mif ses-average/fixels/fc/{ses}.mif -mult ses-average/fixels/fdc/{ses}.mif -force")
    
    if registration != 'rigid':
        metrics = ("fd", "fc", "log_fc", "fdc")
    else:
        metrics = ("fd")
    
    for metric in metrics:
    
        # Mean
        run_command(f"mrmath"
            f" ses-average/fixels/{metric}/{ses1}.mif"
            f" ses-average/fixels/{metric}/{ses2}.mif"
            f" mean"
            f" ses-average/fixels/{metric}/{ses1}_{ses2}_mean.mif"
            f" -force"
            )
            
        # Difference
        run_command(f"mrcalc"
            f" ses-average/fixels/{metric}/{ses2}.mif"
            f" ses-average/fixels/{metric}/{ses1}.mif"
            f" -sub ses-average/fixels/{metric}/{ses2}_min_{ses1}.mif"
            f" -force"
            )
            
        # Half Difference
        run_command(f"mrcalc"
            f" ses-average/fixels/{metric}/{ses2}_min_{ses1}.mif"
            f" 2"
            f" -div ses-average/fixels/{metric}/{ses2}_min_{ses1}_half.mif"
            f" -force"
            )
            
        
        
