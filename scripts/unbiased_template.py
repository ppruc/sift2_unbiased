#!/usr/bin/env python3
"""
unbiased_template.py

Builds a rigid or nonlinear within-subject template from two or more T1w sessions,
using FreeSurfer's robust template registration for unbiased rigid alignment.
Offers optional nonlinear refinement via ANTs SyN or MRtrix3 population_template.
Supports post-hoc transformation of ODFs or multi-contrast ODF registration.

Dependencies:
  - FreeSurfer in $PATH: mri_robust_template, lta_convert
  - ANTs in $PATH: antsMultivariateTemplateConstruction2.sh, antsApplyTransforms
  - MRtrix3 in $PATH: mrtransform, transformconvert, warpconvert, population_template, mrmath, warpinit

Outputs:
  - template_t1w_rigid.nii.gz
  - transforms/{session}/sub2temp_rigid.txt
  - template_t1w_nonlinear.nii.gz (if nonlinear refinement is used)
  - transforms/{session}/temp_rigid2temp_nonlinear.mif (if nonlinear)
  - transforms/{session}/sub2temp_nonlinear.mif (if nonlinear)
  - ODF templates as specified via the --odf argument (first one needs to be the WM FODs if multi-contrast)

Usage:
  python unbiased_template.py \\
    --t1w t1w_ses1.nii.gz t1w_ses2.nii.gz [t1w_ses3...] \\
    --session_labels ses-01 ses-02 [ses-03...] \\
    --out_dir OUTDIR \\
    [--refine_nonlinear [ants|mrtrix3]] \\
    [--odf odf_ses1.mif odf_ses2.mif odf_template.mif] \\
    [--keep_tmp] [--ants_cores N] [--ants_iters N] \\
    [--mrtrix3_masks mask1 mask2 ...] \\
    [--mrtrix3_multicontrast_weights 1 1 ...]

 Examples:
    # Rigid T1w template only
    python unbiased_template.py --t1w t1w_s1.nii.gz t1w_s2.nii.gz --session_labels s1 s2 --out_dir unbiased_template

    # Rigid T1w template, then apply transforms to ODFs and average them
    python unbiased_template.py --t1w t1w_s1.nii.gz t1w_s2.nii.gz --session_labels s1 s2 --out_dir unbiased_template --odf odf_s1.mif odf_s2.mif odf_template.mif

    # ANTs nonlinear T1w template, then apply final warps to ODFs and average them
    python unbiased_template.py --t1w t1w_s1.nii.gz t1w_s2.nii.gz --session_labels s1 s2 --out_dir unbiased_template --refine_nonlinear ants --odf odf_s1.mif odf_s2.mif odf_template.mif --ants_cores 8

    # MRtrix3 nonlinear template using T1w and ODFs in multi-contrast registration
    python unbiased_template.py --t1w t1w_s1.nii.gz t1w_s2.nii.gz --session_labels s1 s2 --out_dir unbiased_template --refine_nonlinear mrtrix3 --odf odf_s1.mif odf_s2.mif odf_template_wmfod.mif --odf odf_s1_gm.mif odf_s2_gm.mif odf_template_gm.mif --mrtrix3_multicontrast_weights 1 1 0.5 --mrtrix3_masks mask_s1.nii.gz mask_s2.nii.gz
"""
import argparse
import shutil
import subprocess
import tempfile
import os
import glob
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_command(cmd, suppress_stderr=False, suppress_stdout=False):
    stderr = subprocess.DEVNULL if suppress_stderr else None
    stdout = subprocess.DEVNULL if suppress_stdout else None

    subprocess.run(
        cmd,
        shell=True,
        check=True,
        stdout=stdout,
        stderr=stderr
    )

def parse_odf_contrasts(odf_args_list_of_lists, n_sessions):
    """
    Parse a list of lists of ODF arguments into structured dicts.
    Each inner list should be: [odf_ses1 ... odf_sesN, output_template]
    """
    if not odf_args_list_of_lists:
        return []

    contrasts = []
    block_size = n_sessions + 1

    for block in odf_args_list_of_lists:
        if len(block) != block_size:
            raise ValueError(
                f"Each --odf block expects {block_size} arguments (N_sessions + 1), "
                f"but got {len(block)} for block: {block}"
            )
        files = block[:n_sessions]
        template_name = block[n_sessions]
        contrasts.append({
            "files": files,
            "template": template_name,
        })
    return contrasts


def robust_template(session_images, work_dir, session_labels):
    """
    Create a rigid within-subject template with FreeSurfer and export transforms.
    Returns template path and dict of session->rigid transform txt.
    """
    transforms_dir = os.path.join(work_dir, "transforms")
    os.makedirs(transforms_dir, exist_ok=True)
    for label in session_labels:
        os.makedirs(os.path.join(transforms_dir, label), exist_ok=True)

    lta_paths = [os.path.join(transforms_dir, label, "sub2temp_rigid.lta") for label in session_labels]
    template_rigid = os.path.join(work_dir, "template_t1w_rigid.nii.gz")

    run_command(
        f"mri_robust_template --mov {' '.join(session_images)} --template {template_rigid} "
        f"--lta {' '.join(lta_paths)} --average 0 -satit"
    )

    rigid_xfms = {}
    for img, label in zip(session_images, session_labels):
        ses_dir = os.path.join(transforms_dir, label)
        lta = os.path.join(ses_dir, "sub2temp_rigid.lta")
        mat = os.path.join(ses_dir, "sub2temp_rigid.mat")
        txt = os.path.join(ses_dir, "sub2temp_rigid.txt")

        run_command(f"lta_convert --inlta {lta} --outfsl {mat}")
        run_command(f"transformconvert {mat} {img} {template_rigid} flirt_import {txt} -force")
        os.remove(mat)
        os.remove(lta)
        rigid_xfms[label] = txt

    return template_rigid, rigid_xfms


def ants_nonlinear_template(session_images, rigid_xfms, work_dir, session_labels, cores, iterations):
    """
    Perform ANTs SyN nonlinear refinement on rigidly-aligned images.
    Returns the nonlinear template and a dict of composed transforms.
    """
    inputs_dir = os.path.join(work_dir, "inputs_ants")
    os.makedirs(inputs_dir, exist_ok=True)

    for img, label in zip(session_images, session_labels):
        out_img = os.path.join(inputs_dir, f"{label}.nii.gz")
        run_command(f"mrtransform {img} {out_img} -linear {rigid_xfms[label]} -force")

    prefix = os.path.join(work_dir, "ants_refined_")
    run_command(
        f"antsMultivariateTemplateConstruction2.sh -d 3 -l 0 -a 1 -n 1 "
        f"-c 2 -j {cores} -i {iterations} -o {prefix} {' '.join(glob.glob(os.path.join(inputs_dir, '*.nii.gz')))}"
    )

    nonlinear_template = os.path.join(work_dir, "template_t1w_nonlinear.nii.gz")
    shutil.copyfile(f"{prefix}template0.nii.gz", nonlinear_template)

    transforms_dir = os.path.join(work_dir, "transforms")
    nl_xfms = {}
    for idx, label in enumerate(session_labels):
        warp_prefix = os.path.join(
            work_dir,
            f"{os.path.basename(prefix)}input{idx:04d}-"
        )

        out_deform = os.path.join(transforms_dir, label, "temp_rigid2temp_nonlinear.mif")
        _convert_warp_ants2mrtrix(nonlinear_template, warp_prefix, out_deform)

        composed = os.path.join(transforms_dir, label, "sub2temp_nonlinear.mif")
        run_command(f"transformcompose {rigid_xfms[label]} {out_deform} {composed} -force")
        nl_xfms[label] = composed

    return nonlinear_template, nl_xfms


def _convert_warp_ants2mrtrix(fixed_img, warp_prefix, out_warp, marker=2147483647):
    """
    Convert ANTs warp + affine to an MRtrix .mif deformation field.

    function is robust to ANTs filenames that include session labels
    between the input index and transform suffix, e.g.:

      ants_refined_input0000-tp2-1Warp.nii.gz
      ants_refined_input0000-tp2-0GenericAffine.mat
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialise identity deformation in template space
        run_command(f"warpinit {fixed_img} {tmpdir}/tmp_identity_warp[].nii -force")

        # Discover ANTs transforms robustly by suffix
        warp_field = glob.glob(f"{warp_prefix}*1Warp.nii.gz")
        affine_mat = glob.glob(f"{warp_prefix}*0GenericAffine.mat")

        if len(warp_field) != 1 or len(affine_mat) != 1:
            raise FileNotFoundError(
                f"Could not uniquely identify ANTs warp components for prefix:\n"
                f"  {warp_prefix}\n"
                f"Found warp fields: {warp_field}\n"
                f"Found affine mats: {affine_mat}"
            )

        warp_field = warp_field[0]
        affine_mat = affine_mat[0]

        # Apply ANTs transforms to each deformation axis
        for axis in range(3):
            run_command(
                f"antsApplyTransforms -d 3 -e 0 "
                f"-i {tmpdir}/tmp_identity_warp{axis}.nii "
                f"-o {tmpdir}/tmp_mrtrix_warp{axis}.nii "
                f"-r {fixed_img} "
                f"-t {warp_field} "
                f"-t {affine_mat} "
                f"--default-value {marker}"
            )

        # Correct and combine into MRtrix deformation field
        run_command(
            f"warpcorrect {tmpdir}/tmp_mrtrix_warp[].nii "
            f"{out_warp} -marker {marker} -force"
        )


def mrtrix_population_template(session_images, rigid_xfms, work_dir, session_labels, odf_contrasts=None, mc_weights=None, masks=None):
    """
    Run MRtrix3 population_template for T1w-only or multi-contrast.
    Returns the nonlinear template and a dict of composed transforms.
    """
    inputs_dir = os.path.join(work_dir, "inputs_mrtrix")
    os.makedirs(inputs_dir, exist_ok=True)

    # Prepare T1w inputs (rigidly aligned)
    t1w_dir = os.path.join(inputs_dir, "T1w")
    os.makedirs(t1w_dir, exist_ok=True)
    for img, label in zip(session_images, session_labels):
        out_img = os.path.join(t1w_dir, f"{label}.nii.gz")
        run_command(f"mrtransform {img} {out_img} -linear {rigid_xfms[label]} -force")

    cmd = ["population_template", t1w_dir, os.path.join(work_dir, "template_t1w_nonlinear.nii.gz")]

    # Multi-contrast handling
    if odf_contrasts:
        logging.info("Preparing multi-contrast inputs for MRtrix3...")
        for idx, contrast in enumerate(odf_contrasts, start=1):
            odf_dir = os.path.join(inputs_dir, f"odf_multicontrast_{idx}")
            os.makedirs(odf_dir, exist_ok=True)
            for img, label in zip(contrast["files"], session_labels):
                out_odf = os.path.join(odf_dir, f"{label}.mif")
                # Try mrtransform with -reorient_fod yes, fallback to without if it fails
                try:
                    run_command(
                        f"mrtransform {img} {out_odf} -linear {rigid_xfms[label]} -reorient_fod yes -force -quiet",
                        suppress_stderr=True
                    )
                except subprocess.CalledProcessError:
                    logging.warning(
                        f"FOD reorientation not possible for {img}; assuming it is not FOD input, so retrying with -reorient_fod no"
                    )
                    run_command(
                        f"mrtransform {img} {out_odf} -linear {rigid_xfms[label]} -reorient_fod no -force -quiet"
                    )
            
            # The template path needs to be absolute for population_template to write it
            cmd.extend([odf_dir, os.path.join(work_dir, os.path.basename(contrast["template"]))]) # Use basename for internal consistency, copy later
        
        w_str = ",".join(map(str, mc_weights))
        cmd.extend(["-mc_weight_affine", w_str, "-mc_weight_nl", w_str, "-type", "affine_nonlinear", "-initial_alignment", "none"])

    if masks:
        mask_dir = os.path.join(inputs_dir, "mask")
        os.makedirs(mask_dir, exist_ok=True)
        for img, label in zip(masks, session_labels):
            out_mask = os.path.join(mask_dir, f"{label}.nii.gz")
            run_command(f"mrtransform {img} {out_mask} -linear {rigid_xfms[label]} -interp nearest -force")
        cmd.extend(["-mask_dir", mask_dir, "-template_mask", os.path.join(work_dir, "template_mask.nii.gz")])

    warp_dir = os.path.join(work_dir, "warps")
    cmd.extend(["-warp_dir", warp_dir, "-force"])
    run_command(" ".join(cmd))

    # Convert and compose warps
    transforms_dir = os.path.join(work_dir, "transforms")
    template_nl = os.path.join(work_dir, "template_t1w_nonlinear.nii.gz")
    nl_xfms = {}
    for label in session_labels:
        warp_full = os.path.join(warp_dir, f"{label}.mif")
        deform = os.path.join(transforms_dir, label, "temp_rigid2temp_nonlinear.mif")
        composed = os.path.join(transforms_dir, label, "sub2temp_nonlinear.mif")
        run_command(f"warpconvert {warp_full} warpfull2deformation {deform} -template {template_nl} -force")
        run_command(f"transformcompose {rigid_xfms[label]} {deform} {composed} -force")
        nl_xfms[label] = composed

    return template_nl, nl_xfms

def get_voxel_size(image_path):
                result = subprocess.run(
                    ["mrinfo", image_path, "-spacing"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                spacing_values = result.stdout.strip().split()
                return spacing_values[0]  # Return the first voxel size (e.g., '1.25')

def apply_transforms_and_average_odfs(odf_contrasts, final_transforms, session_labels, work_dir, out_dir, is_nonlinear):
    """
    Applies final transforms to ODFs and averages them into template space.
    Used for rigid-only and ANTs pipelines.
    """
    logging.info("Applying transforms to ODFs and creating ODF templates...")
    odf_tmp_dir = os.path.join(work_dir, "odf_transformed")
    os.makedirs(odf_tmp_dir, exist_ok=True)
    
    transform_opt = "-warp" if is_nonlinear else "-linear"

    for i, contrast in enumerate(odf_contrasts):
        logging.info(f"  Processing ODF contrast {i+1}/{len(odf_contrasts)} -> {os.path.join(out_dir, contrast['template'])}")
        transformed_files = []
        
        # For linear transforms, create a regridded template at ODF resolution
        template_for_resampling = None
        if not is_nonlinear:
            # Get target resolution from first ODF image
            first_odf = contrast["files"][0]
            regridded_template = os.path.join(odf_tmp_dir, f"rigid_t1w_template_regrid_contrast-{i}.nii.gz")
            rigid_template = os.path.join(work_dir, "template_t1w_rigid.nii.gz")

            # Extract voxel size from ODF image and regrid the rigid template
            target_vox = get_voxel_size(first_odf)
            
            run_command(f"mrgrid {rigid_template} regrid {regridded_template} -vox {target_vox} -force")
            template_for_resampling = regridded_template
        
        for odf_in, label in zip(contrast["files"], session_labels):
            xfm = final_transforms[label]
            odf_out = os.path.join(odf_tmp_dir, f"{label}_contrast-{i}.mif")
            
            cmd_parts = [f"mrtransform {odf_in} {odf_out} {transform_opt} {xfm}"]
            cmd_parts.append("-reorient_fod yes")
            
            if not is_nonlinear:
                # For linear transforms add template resampling
                cmd_parts.append(f"-template {template_for_resampling}")
            
            cmd_parts.append("-force")
            run_command(" ".join(cmd_parts))
            transformed_files.append(odf_out)
        
        out_template_path = os.path.join(out_dir, contrast['template'])
        run_command(f"mrmath -force {' '.join(transformed_files)} mean {out_template_path} -keep_unary_axes")

def main():
    parser = argparse.ArgumentParser(
        description="Unbiased template builder: rigid alignment with optional nonlinear refinement (ANTs/MRtrix3).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--t1w", nargs='+', required=True, help="T1w images for each session (>=2). Must match order of --session_labels.")
    parser.add_argument("--session_labels", nargs='+', required=True, help="Matching labels for each session (e.g. ses-01).")
    parser.add_argument("--out_dir", required=True, help="Directory to write outputs.")
    parser.add_argument("--refine_nonlinear", choices=["ants", "mrtrix3"], default=None, help="Optionally perform nonlinear refinement. If not set, only a rigid template is created.")
    
    parser.add_argument(
        "--odf",
        nargs='+',  # Each --odf expects multiple arguments (session files + template name)
        action='append', # Accumulate these lists if --odf is provided multiple times
        default=[],      # Ensure it's always a list, even if not provided
        help="Define ODF contrasts. For each, provide all session ODFs followed by the output template name.\n"
             "Example: --odf odf_s1.mif odf_s2.mif odf_template.mif --odf odf_s1_2.mif odf_s2_2.mif odf_template_2.mif"
    )
    
    parser.add_argument("--mrtrix3_multicontrast_weights", nargs='+', type=float, default=None, help="Registration weights for MRtrix3 multi-contrast. Provide one weight for T1w, followed by one for each ODF contrast. E.g., --mrtrix3_multicontrast_weights 1 1 0.5")
    parser.add_argument("--mrtrix3_masks", nargs='+', default=None, help="Optional masks for MRtrix3 multi-contrast.")
    parser.add_argument("--keep_tmp", action="store_true", help="Retain intermediate files in a tmp_* directory.")
    parser.add_argument("--ants_cores", type=int, default=8, help="Threads for ANTs registration.")
    parser.add_argument("--ants_iters", type=int, default=4, help="Iterations for ANTs template construction.")

    args = parser.parse_args()

    # --- Validation ---
    if len(args.t1w) < 2:
        parser.error("Require at least two --t1w images.")
    if len(args.session_labels) != len(args.t1w):
        parser.error("--session_labels count must match --t1w count.")
    
    odf_contrasts = parse_odf_contrasts(args.odf, len(args.t1w))
    
    if args.refine_nonlinear == 'mrtrix3' and odf_contrasts:
        if not args.mrtrix3_multicontrast_weights:
            parser.error("--mrtrix3_multicontrast_weights is required for MRtrix3 multi-contrast ODF registration.")
        expected_weights = 1 + len(odf_contrasts) # This logic remains correct
        if len(args.mrtrix3_multicontrast_weights) != expected_weights:
            parser.error(f"--mrtrix3_multicontrast_weights must provide one weight for T1w plus one for each ODF contrast. Expected {expected_weights}, got {len(args.mrtrix3_multicontrast_weights)}.")
    elif args.mrtrix3_multicontrast_weights and args.refine_nonlinear != 'mrtrix3':
        logging.warning("--mrtrix3_multicontrast_weights is only used with --refine_nonlinear=mrtrix3. Ignoring.")

    # --- Setup ---
    os.makedirs(args.out_dir, exist_ok=True)
    work_dir = tempfile.mkdtemp(prefix="tmp_", dir=args.out_dir)
    logging.info(f"Using temporary work dir: {work_dir}")

    # --- Step 1: Rigid Template (Always Run) ---
    logging.info("--- [1/2] Building rigid T1w template ---")
    template_rigid, rigid_xfms = robust_template(args.t1w, work_dir, args.session_labels)
    shutil.copy(template_rigid, os.path.join(args.out_dir, "template_t1w_rigid.nii.gz"))
    
    final_transforms = rigid_xfms
    is_nonlinear = False

    # --- Step 2: Nonlinear Refinement (Optional) ---
    if args.refine_nonlinear:
        logging.info(f"--- [2/2] Performing {args.refine_nonlinear.upper()} nonlinear refinement ---")
        is_nonlinear = True
        if args.refine_nonlinear == "ants":
            template_nl, nl_xfms = ants_nonlinear_template(
                args.t1w, rigid_xfms, work_dir,
                args.session_labels, args.ants_cores, args.ants_iters
            )
            final_transforms = nl_xfms
        elif args.refine_nonlinear == "mrtrix3":
            template_nl, nl_xfms = mrtrix_population_template(
                args.t1w, rigid_xfms, work_dir, args.session_labels, 
                odf_contrasts=odf_contrasts, 
                mc_weights=args.mrtrix3_multicontrast_weights, 
                masks=args.mrtrix3_masks
            )
            final_transforms = nl_xfms
        shutil.copy(template_nl, os.path.join(args.out_dir, "template_t1w_nonlinear.nii.gz"))

    # --- Finalize Transforms & Process ODFs ---
    logging.info("--- Finalizing outputs ---")
    shutil.copytree(os.path.join(work_dir, "transforms"), os.path.join(args.out_dir, "transforms"), dirs_exist_ok=True)

    if odf_contrasts:
        if args.refine_nonlinear == 'mrtrix3':
            # For MRtrix3, copy the generated ODF templates from work_dir to out_dir
            logging.info("Copying MRtrix3-generated ODF templates...")
            for contrast in odf_contrasts:
                # Need to reconstruct the path, as population_template uses basenames
                src = os.path.join(work_dir, os.path.basename(contrast['template'])) 
                dst = os.path.join(args.out_dir, os.path.basename(contrast['template']))
                if os.path.exists(src):
                    shutil.copy(src, dst)
                else:
                    logging.warning(f"Could not find expected ODF template {src} to copy.")
        else:
            # For rigid/ANTs, apply transforms and average ODFs
            apply_transforms_and_average_odfs(
                odf_contrasts, final_transforms, args.session_labels,
                work_dir, args.out_dir, is_nonlinear
            )

    # --- Cleanup ---
    if not args.keep_tmp:
        shutil.rmtree(work_dir)
        logging.info("Temporary work dir removed.")
    else:
        logging.info(f"Temporary work dir retained at {work_dir}")

    logging.info("Template build complete. Outputs in %s", args.out_dir)

if __name__ == "__main__":
    main()