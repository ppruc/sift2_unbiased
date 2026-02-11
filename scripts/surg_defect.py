import os
import subprocess
import argparse
import tempfile
import shutil


def run_command(command, log=None):
    try:
        if log is not None:
            with open(log, "w") as log_file:
                result = subprocess.run(
                    command,
                    shell=True,
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
        else:
            subprocess.run(command, shell=True)
    except Exception as e:
        print(f"Command '{command}' failed with error: {e}")


def segment_lesion(input_preop: str,
                   input_postop: str,
                   output_mask: str,
                   mask_preop: str = None,
                   mask_postop: str = None,
                   use_n4: bool = False,
                   keep_tmp: bool = False,
                   subsegment: bool = False):
    """
    Segments a lesion (surgical defect) from two coregistered T1w images.

    Args:
        input_preop (str): Path to the preoperative T1w image.
        input_postop (str): Path to the postoperative T1w image.
        output_mask (str): Path to save the final defect mask.
        mask_preop (str, optional): Preoperative brain mask for cropping.
        mask_postop (str, optional): Postoperative brain mask for cropping.
        use_n4 (bool): If True, run bias correction via antsAtroposN4.
        keep_tmp (bool): If True, retain temporary files in output_dir.
        subsegment (bool): If True, perform subsegmentation on defect.
    """
    # Determine tmp_dir location based on output_mask path
    out_dir = os.path.dirname(os.path.abspath(output_mask))
    tmp_dir = tempfile.mkdtemp(prefix="lesionseg_tmp_", dir=out_dir)

    def tmp(name):
        return os.path.join(tmp_dir, name)

    try:
        # 1) Resample inputs
        for img, tag in [(input_preop, 'preop'), (input_postop, 'postop')]:
            run_command(
                f"antsApplyTransforms -d 3 -i {img} -r {input_postop}"
                f" -o {tmp(f'T1w_{tag}.nii.gz')} -n NearestNeighbor"
            )

        # 2) Resample masks
        for mask, tag in [(mask_preop, 'preop'), (mask_postop, 'postop')]:
            if mask:
                run_command(
                    f"antsApplyTransforms -d 3 -i {mask} -r {input_postop}"
                    f" -o {tmp(f'mask_{tag}.nii.gz')} -n NearestNeighbor"
                )

        # 3) Segment and smooth CSF
        for tag in ('preop', 'postop'):
            img = tmp(f'T1w_{tag}.nii.gz')
            mask_opt = tmp(f'mask_{tag}.nii.gz') if (mask_preop if tag=='preop' else mask_postop) else ''
            xarg = f"-x {mask_opt}" if mask_opt else ''

            if use_n4:
                run_command(
                    f"antsAtroposN4.sh -d 3 -a {img} {xarg}"
                    f" -o {tmp(f'seg_{tag}')} -c 3"
                )
            else:
                run_command(
                    f"Atropos -d 3 -a {img} {xarg}"
                    f" -o '[{tmp('seg_'+tag+'.nii.gz')},{tmp('seg_'+tag+'SegmentationPosteriors%d.nii.gz')}]'"
                    f" -i 'KMeans[3]' -m '[0.1,1x1x1]' -c '[5,0.001]' -r 1 -v"
                )
                
            post_prefix = tmp(f'seg_{tag}SegmentationPosteriors')

            run_command(
                f"mrfilter {post_prefix}1.nii.gz smooth {tmp(f'csf_{tag}_smooth.nii.gz')} -force"
            )

        # 4) Compute CSF diff
        run_command(
            f"mrcalc {tmp('csf_postop_smooth.nii.gz')} {tmp('csf_preop_smooth.nii.gz')}"
            f" -sub {tmp('csf_diff.nii.gz')} -force"
        )

        # 5) Mask intersection
        if mask_preop and mask_postop:
            run_command(
                f"mrmath {tmp('mask_preop.nii.gz')} {tmp('mask_postop.nii.gz')}"
                f" min {tmp('mask_intersection.nii.gz')} -force"
            )
            run_command(
                f"mrcalc {tmp('csf_diff.nii.gz')} {tmp('mask_intersection.nii.gz')}"
                f" -mult {tmp('csf_diff_masked.nii.gz')} -force"
            )
        else:
            run_command(
                f"mrconvert {tmp('csf_diff.nii.gz')} {tmp('csf_diff_masked.nii.gz')} -force"
            )

        # 6) Threshold + morphology
        run_command(
            f"mrthreshold {tmp('csf_diff_masked.nii.gz')} {tmp('csf_diff_thresh.nii.gz')} -abs 0.2 -force"
        )
        run_command(
            f"maskfilter {tmp('csf_diff_thresh.nii.gz')} erode {tmp('csf_diff_eroded.nii.gz')} -force"
        )
        run_command(
            f"maskfilter {tmp('csf_diff_eroded.nii.gz')} connect {tmp('csf_diff_largest.nii.gz')} -largest -force"
        )
        run_command(
            f"maskfilter {tmp('csf_diff_largest.nii.gz')} dilate {tmp('csf_diff_clean.nii.gz')} -force"
        )

        # 7) Preop tissue mask
        run_command(
            f"mrcalc {tmp('seg_preopSegmentationPosteriors2.nii.gz')} {tmp('seg_preopSegmentationPosteriors3.nii.gz')}"
            f" -add {tmp('preop_tissue.nii.gz')} -force"
        )
        run_command(
            f"mrfilter {tmp('preop_tissue.nii.gz')} smooth {tmp('preop_tissue_smooth.nii.gz')} -force"
        )
        run_command(
            f"mrthreshold {tmp('preop_tissue_smooth.nii.gz')} {tmp('preop_tissue_thresh.nii.gz')} -abs 0.2 -force"
        )

        # 8) Final mask
        run_command(
            f"mrcalc {tmp('csf_diff_clean.nii.gz')} {tmp('preop_tissue_thresh.nii.gz')}"
            f" -mult {tmp('surg_defect_c1_c2.nii.gz')} -force"
        )

        # 9) Optional subsegment
        if subsegment:
            run_command(
                f"Atropos -d 3 -a {tmp('T1w_postop.nii.gz')} -x {tmp('surg_defect_c1_c2.nii.gz')}"
                f" -o '[{tmp('surg_defect_subseg.nii.gz')},{tmp('surg_defect_subsegPosteriors%d.nii.gz')}]'"
                f" -i 'KMeans[2]' -m '[0.1,1x1x1]' -c '[5,0.001]' -r 1 -v"
            )
            for i, comp in enumerate(('c1','c2'), start=1):
                run_command(
                    f"mrthreshold {tmp(f'surg_defect_subsegPosteriors{i}.nii.gz')} "
                    f"{tmp(f'subseg_{comp}_thresh.nii.gz')} -abs 0.2 -force"
                )
                run_command(
                    f"maskfilter {tmp(f'subseg_{comp}_thresh.nii.gz')} erode "
                    f"{tmp(f'subseg_{comp}_eroded.nii.gz')} -force"
                )
                run_command(
                    f"maskfilter {tmp(f'subseg_{comp}_eroded.nii.gz')} connect "
                    f"{tmp(f'subseg_{comp}_largest.nii.gz')} -largest -force"
                )
                run_command(
                    f"maskfilter {tmp(f'subseg_{comp}_largest.nii.gz')} dilate "
                    f"{tmp(f'surg_defect_{comp}.nii.gz')} -force"
                )
        
        # Write final output mask to requested location
        if subsegment:
            run_command(f'mrconvert {tmp("surg_defect_c1.nii.gz")} {output_mask} -force')
        else:
            run_command(f'mrconvert {tmp("surg_defect_c1_c2.nii.gz")} {output_mask} -force')

        print(f"Lesion mask written to: {output_mask}")

    finally:
        if not keep_tmp:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        else:
            print(f"Temporary files kept in: {tmp_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Segment surgical lesion between two T1w images')
    parser.add_argument('--preop', required=True, help='Preoperative T1w image')
    parser.add_argument('--postop', required=True, help='Postoperative T1w image')
    parser.add_argument('--mask-preop', help='Optional preoperative brain mask')
    parser.add_argument('--mask-postop', help='Optional postoperative brain mask')
    parser.add_argument('--out-mask', required=True, help='Final lesion mask path')
    parser.add_argument('--use-n4', action='store_true', help='Enable N4 bias correction')
    parser.add_argument('--keep-tmp', action='store_true', help='Keep temporary files')
    parser.add_argument('--subsegment', action='store_true', default=True, help='Perform subsegmentation (default: True)')
    args = parser.parse_args()

    segment_lesion(
        input_preop=args.preop,
        input_postop=args.postop,
        output_mask=args.out_mask,
        mask_preop=args.mask_preop,
        mask_postop=args.mask_postop,
        use_n4=args.use_n4,
        keep_tmp=args.keep_tmp,
        subsegment=args.subsegment
    )