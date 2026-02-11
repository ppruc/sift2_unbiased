import os
import sys
from joblib import Parallel, delayed

sys.path.append(os.path.abspath('/path/to/functions/')) # can be found in git repository (./code/in_vivo/functions)
from make_derivatives import make_derivatives
from get_sessions import get_sessions
from response_functions import response_functions
from prepare_anat import prepare_anat
from csd import csd
from robust_template import robust_template
from refine_template_ants import refine_template_ants
from surg_defect import surg_defect
from surg_defect_manual_corr import surg_defect_manual_corr
from wmfod_template import wmfod_template
from impute_template import impute_template
from recon_cross import recon_cross
from tck_template import tck_template
from fixels_session import fixels_session
from fixels_template import fixels_template
from tck_session import tck_session
from recon_base_autorecon_1 import recon_base_autorecon_1
from recon_base_autorecon_2_3 import recon_base_autorecon_2_3
from recon_long import recon_long
from anatomical_stats_modified import anatomical_stats_modified
from atlas_template import atlas_template
from atlas_session import atlas_session
from sift2_cross import sift2_cross
from sift2_template import sift2_template
from sift2_symmetric import sift2_symmetric
from sift2_differential import sift2_differential
from sift2_none import sift2_none
from sift2_results import sift2_results
from stats_connectome import stats_connectome

dataset = "Templobe_Surgery"
bids_dir = os.path.join("/path/to/dataset/BIDS/")
derivatives_dir = os.path.join(bids_dir,"derivatives")
dependencies_dir = os.path.join(bids_dir,"path/to/dependencies") # can be found in git repository (./code/in_vivo/dependencies)
subs = [item for item in os.listdir(derivatives_dir) if item.startswith("sub-")]
tasks = [(sub, ses) for sub in subs for ses in get_sessions(derivatives_dir, sub)]

# Number of tracks
ntcks="10M"

# Define regularisation basis, function, and strength for each pipeline
params_cross = ("streamline", "gamma", 0.1)
params_temp = ("streamline", "gamma", 0.1)
params_sym = ("streamline", "gamma", 0.1)
params_diff = ("streamline", "dualinvbarr", 0.1)
reg_basis_cross, reg_fn_cross, reg_strength_cross = params_cross
reg_basis_temp, reg_fn_temp, reg_strength_temp = params_temp
reg_basis_sym, reg_fn_sym, reg_strength_sym = params_sym
reg_basis_diff, reg_fn_diff, reg_strength_diff = params_diff

make_derivatives(bids_dir) # Create output folder structure
response_functions(derivatives_dir, subs) # estimate tissue response functions from dwi
for sub in subs:
    for ses in get_sessions(derivatives_dir, sub):
        csd(derivatives_dir, sub, ses, ss3t=True) # derive ODFs (SS3T)
        prepare_anat(derivatives_dir, sub, ses)  # preprocess/register T1w to DWI
    robust_template(derivatives_dir, sub) # rigid T1w within-subject template registration
    refine_template_ants(derivatives_dir, sub, cores=30, use_bet=False, fs_conform_inputs=True, final_template=True) # non-linear refinement of the T1w within-subject template registration
    surg_defect(derivatives_dir,sub) # segment surgical defect
    impute_template(derivatives_dir,sub) # create anatomically intact template by imputing preoperative tissue into resection zone
    wmfod_template(derivatives_dir,sub,'nonlinear',surgical=True)  # apply transforms to WMFODs and generate template

# Longitudinal FreeSurfer Pipeline run in parallel
Parallel(n_jobs=27, backend='multiprocessing')(delayed(recon_cross)(derivatives_dir, sub, ses,remove_old_run=False) for sub, ses in tasks)
Parallel(n_jobs=18, backend='multiprocessing')(delayed(recon_base_autorecon_1)(derivatives_dir, sub, remove_old_run=True) for sub in subs)
Parallel(n_jobs=18, backend='multiprocessing')(delayed(recon_base_autorecon_2_3)(derivatives_dir, sub, inject_template=True) for sub in subs)
#Parallel(n_jobs=18, backend='multiprocessing')(delayed(recon_long)(derivatives_dir, sub, ses) for sub, ses in tasks) # not needed for this study; provides longitudinal grey matter measurements

for sub in subs:
    for ses in get_sessions(derivatives_dir,sub):
        fixels_session(derivatives_dir,sub,ses) # segment fixels for sessions
        tck_session(derivatives_dir, sub, ses, ntcks, surgical=True)  # run cross-sectional tractography
        atlas_session(derivatives_dir, dependencies_dir, sub, ses, surgical=True) # derive parcellations for sessions

    fixels_template(derivatives_dir, sub,'nonlinear') # segment fixels for template
    tck_template(derivatives_dir, sub, ntcks, surgical=True) # run template tractography
    anatomical_stats_modified(derivatives_dir, sub, dependencies_dir) # remove resected vertices from FreeSurfer segmentations
    atlas_template(derivatives_dir, dependencies_dir, sub, surgical=True) # derive parcellation for template
   
    # Pipelines 1-4
    for ses in get_sessions(derivatives_dir, sub):
        # Pipeline 1
        sift2_none(derivatives_dir, sub, ses, ntcks, "fd",surgical=True) 
        
        # Pipeline 2
        sift2_cross(derivatives_dir, sub, ses, ntcks, "fd", reg_basis_cross=reg_basis_cross, reg_fn_cross=reg_fn_cross, reg_strength_cross=reg_strength_cross,surgical=True)

    # Unbiased Template
    sift2_template(derivatives_dir,sub,ntcks,"fdc",reg_fn_temp=reg_fn_temp,reg_basis_temp=reg_basis_temp,reg_strength_temp=reg_strength_temp,surgical=True)
   
    # Pipeline 3
    sift2_symmetric(derivatives_dir, sub, ses, ntcks, "fdc", reg_basis_temp=reg_basis_temp, reg_fn_temp=reg_fn_temp, reg_strength_temp=reg_strength_temp, reg_basis_sym=reg_basis_sym, reg_fn_sym=reg_fn_sym, reg_strength_sym=reg_strength_sym,surgical=True)
    
    # Pipeline 4
    sift2_differential(derivatives_dir, sub,ntcks,"fdc",reg_fn_temp=reg_fn_temp,reg_basis_temp=reg_basis_temp,reg_strength_temp=reg_strength_temp,reg_basis_diff=reg_basis_diff,reg_fn_diff=reg_fn_diff,reg_strength_diff=reg_strength_diff,surgical=True)

sift2_results(derivatives_dir, subs, ntcks, params_cross, params_temp, params_sym, params_diff) # collects the connectomics results and writes them to a folder "sift2_results"
stats_connectome(derivatives_dir,ntcks,algorithm="tfnbs",nonstationarity=False,surgical=True) # requires design_matrix and contrast files to be defined in "template" directory

