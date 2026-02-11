import sys
import os

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def response_functions(derivatives_dir, subs):
    
    os.chdir(derivatives_dir)
    os.makedirs("tmp_response")
    for sub in subs:
        for ses in get_sessions(derivatives_dir, sub):
            run_command(f"dwi2response dhollander {sub}/{ses}/dwi/dwi.mif {sub}/{ses}/dwi/response_wm.txt {sub}/{ses}/dwi/response_gm.txt {sub}/{ses}/dwi/response_csf.txt")
            for tissue in ("wm", "gm", "csf"):
                run_command(f"cp {sub}/{ses}/dwi/response_{tissue}.txt tmp_response/response_{tissue}_{sub}_{ses}.txt")
    for tissue in ("wm", "gm", "csf"):
        run_command(f"responsemean tmp_response/response_{tissue}* group_average_response_{tissue}.txt")
        
    run_command(f"rm -r tmp_response")
   
