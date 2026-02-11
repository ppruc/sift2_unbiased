# PART 1: PRE-PROCESSING AND CONSTRAINED SPHERICAL DECONVOLUTION

## 1.1 Denoising and unringing

**\[standard processing\]**

If denoising and/or Gibbs ringing removal are performed as part of the
preprocessing, they *must* be performed *prior* to any other processing
steps: most other processing steps, in particular those that involve
interpolation of the data, will invalidate the original properties of
the image data that are exploited
by [```dwidenoise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwidenoise.html#dwidenoise) and [```mrdegibbs```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mrdegibbs.html#mrdegibbs) at
this stage, and would render the result prone to errors [\[Tahedl2025\]](https://www.nature.com/articles/s41596-024-01129-1).

If denoising is included, it's performed as the first step:

```bash
for_each tp* : dwidenoise IN/dwi.mif IN/dwi_denoised.mif
```

If Gibbs ringing removal is included, it follows immediately after:

```bash
for_each tp* : mrdegibbs \
  IN/dwi_denoised.mif \
  IN/dwi_denoised_unringed.mif \
  -axes 0,1
```

> [!WARNING]
> If image slices are not *axial* but *coronal* or *sagittal* (assuming a
> typical human scanner and subject), the `-axes` option must be adapted
> accordingly (see [```mrdegibbs```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mrdegibbs.html)
> documentation for more information).

## 1.2 Motion and distortion correction

**\[standard processing\]**

The [```dwifslpreproc```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwifslpreproc.html#dwifslpreproc) command
handles motion and distortion correction for DWI data (including eddy
current distortions and optionally susceptibility-induced EPI
distortions). Even though the command works seamlessly like any
other *MRtrix3* command, it is in fact a script that interfaces with
the [```FSL```](http://fsl.fmrib.ox.ac.uk/) package to perform most of its
core functionality and algorithms. For this command to
work, [```FSL```](http://fsl.fmrib.ox.ac.uk/) (including [```eddy```](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy))
needs to be installed. Also remember to cite the relevant articles with
respect to the specific algorithms (see
the [```dwifslpreproc```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwifslpreproc.html#dwifslpreproc) help
page).

The simplest scenario is to (only) correct for motion and eddy
current-induced distortions:

```bash
for_each tp* : dwifslpreproc \
  IN/dwi_denoised_unringed.mif \
  IN/dwi_denoised_unringed_preproc.mif \
  -rpe_none \
  -pe_dir AP
```

> [!WARNING]
> If the phase-encoding direction of the acquisition is not
> anterior–posterior but left–right or superior–inferior, the `-pe` option
> must be adapted accordingly (see the
> [```dwifslpreproc```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwifslpreproc.html#dwifslpreproc)
> documentation).  
>
> For advanced scenarios and acquisitions (e.g. correcting for
> susceptibility-induced EPI distortions using a pair of reverse
> phase-encoded *b*=0 images), refer to the
> [DWI distortion correction using ```dwifslpreproc```](https://mrtrix.readthedocs.io/en/latest/dwi_preprocessing/dwifslpreproc.html#dwifslpreproc-page)
> section and the
> [```dwifslprepro```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwifslpreproc.html#dwifslpreproc)
> documentation.

> [!TIP]
> To correct for susceptibility-induced EPI distortions in the absence of
> reverse phase-encoding *b*=0 images, it is possible to [synthesise a
> distortion-free b0 image for
> correction](https://github.com/MASILab/Synb0-DISCO). Through this image,
> the susceptibility field can be estimated using topup, and the relevant
> files provided via the ```-topup_files``` option available in [an updated
> version of ```dwifslpreproc```](https://github.com/MRtrix3/mrtrix3/tree/dev)


## 1.3 Bias field correction

**\[standard processing\]**

This multi-tissue pipeline corrects for bias fields (and jointly
performs global intensity normalisation) at the
upcoming [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise) step.
The only incentive for running the (less robust and
accurate) [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect) at
this stage in the pipeline is *to improve brain mask estimation* (at the
later [```dwi2mask```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwi2mask.html#dwi2mask) step,
in case severe bias fields are present in the data). However, cases have
been reported where
running [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect) at
this stage resulted in *inferior* brain mask estimation later on. This
is probably more likely in case bias fields are not as strongly present
in the data.
Whether [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect) is
run at this stage or not, does not have any significant impact on the
performance
of [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise) later
on.

If or when performing DWI bias field correction at this stage, it is
achieved by first estimating the bias field from the DWI b=0 data, then
applying the field to correct all DW volumes, which is done in a single
step using the ants algorithm within
the [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect) script
in *MRtrix3*. The script uses a bias field correction algorithm
available in [```ANTs```](http://stnava.github.io/ANTs/) (the N4
algorithm). *Don't* use the ```fsl``` algorithm with this script in this
analysis pipeline. To perform bias field correction on DW images, run:


```bash
for_each tp* : dwibiascorrect ants \
  IN/dwi_denoised_unringed_preproc.mif \
  IN/dwi_denoised_unringed_preproc_unbiased.mif
```

> [!WARNING]
> If the pipeline is run on single-shell dMRI data, please refer to the
> relevant global intensity normalisation steps of the
> [single-tissue Fixel-Based Analysis](https://mrtrix.readthedocs.io/en/latest/fixel_based_analysis/st_fibre_density_cross-section.html)
> tutorial.



## 1.4 Response function estimation

### 1.4.1 Computing session-specific tissue response functions 

**\[standard processing\]**

A robust and fully automated unsupervised method to obtain 3-tissue
response functions representing single-fibre white matter, grey matter
and CSF from the data itself, is the approach proposed
in [\[Dhollander2016b\]](https://mrtrix.readthedocs.io/en/latest/reference/references.html#dhollander2016b) with
the improvements
of [\[Dhollander2019\]](https://mrtrix.readthedocs.io/en/latest/reference/references.html#dhollander2019),
which can be run by:

```bash
for_each tp* : dwi2response dhollander \
  IN/dwi_denoised_unringed_preproc_unbiased.mif \
  IN/response_wm.txt \
  IN/response_gm.txt \
  IN/response_csf.txt
```

### 1.4.2 Computing session-average tissue response functions 

**\[standard processing\]**

It is crucial for longitudinal FBC quantification to only use a
single *unique* set of the (three) response functions to perform
(3-tissue) spherical deconvolution of all sessions: as the
(3-tissue) spherical deconvolution results will be expressed in function
of this set of response functions, they can (in an abstract way) be seen
as the units of both the final apparent fibre density metric and the
other compartments estimated in the model. One possible way to obtain a
unique set of response functions, is to average the response functions
obtained from all sessions for each tissue type:

```bash
responsemean */response_wm.txt session_mean_response_wm.txt

responsemean */response_gm.txt session_mean_response_gm.txt

responsemean */response_csf.txt session_mean_response_csf.txt
```

There is however no strict requirement for the final set of response
functions to be the average of all sessions, for each tissue
type (or indeed, it doesn't even have to be the average per se). In
certain very specific cases, it may even be wise to leave out
sessions (for this step) where the response functions could not
reliably be obtained, or where pathology affected the brain globally.



### 1.4.3 Computing cohort-average tissue response functions

**\[standard processing\]**

If the goal of the intended analysis is to derive robust longitudinal
FBC estimates that are comparable not only between sessions but also
between subjects, it is important to derive a single unique set of
response functions for the entire cohort that can then be used for
derivation of FODs. Assuming that all the previous steps have also been
 executed for other subjects in a dataset, this can be achieved by
averaging the session-average response function across subjects.

```bash
cd ..

responsemean */session_mean_response_wm.txt group_mean_response_wm.txt

responsemean */session_mean_response_gm.txt group_mean_response_gm.txt

responsemean */session_mean_response_csf.txt group_mean_response_csf.txt

cd sub-exemplar
```


## 1.5 Upsampling DWI images

**\[standard processing\]**

Upsampling DWI data *before* computing FODs increases anatomical
contrast and improves downstream within-subject template building,
registration, and quantitative tractography (if your original resolution
is already higher, you can skip this step):

```bash
for_each tp* : mrgrid \
  IN/dwi_denoised_unringed_preproc_unbiased.mif \
  regrid \
  -vox 1.25 \
  IN/dwi_denoised_unringed_preproc_unbiased_upsampled.mif
```

## 1.6 Compute upsampled brain mask images

**\[standard processing\]**

Compute a whole brain mask from the upsampled DW images:

```bash
for_each tp* : dwi2mask \
  IN/dwi_denoised_unringed_preproc_unbiased_upsampled.mif \
  IN/dwi_mask_upsampled.mif
```

> [!WARNING]
> It is absolutely **crucial** at this stage to check that *all* individual
> session masks include *all* regions of the brain that are intended to be
> analysed. Fibre orientation distributions will *only* be computed within
> these masks; and at a later step (in within-subject template space) the
> analysis mask will be restricted to the *intersection* of all masks.  
>
> As a result, *any* individual session mask that excludes a given region
> will cause this region to be excluded from the analysis (unless a more
> advanced pipeline is followed; see
> [Mitigating the effects of brain cropping](https://mrtrix.readthedocs.io/en/latest/fixel_based_analysis/mitigating_brain_cropping.html#mitigating-brain-cropping)).  
>
> Masks that appear overly generous or that include some non-brain regions
> generally do **not** cause concerns at this stage. Hence, if in doubt, it is
> advised to always err on the side of *inclusion* of regions.

> [!NOTE]
> The earlier
> [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect)
> step is not fundamentally important in the multi-tissue FBC analysis
> pipeline, as the later
> [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise)
> step performs more robustly. If
> [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect)
> is included, 
> [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise)
> will typically further improve the result.  
>
> While performing the earlier
> [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect)
> step typically improves
> [```dwi2mask```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwi2mask.html#dwi2mask)
> performance, cases have been observed where the opposite is true
> (typically if the data contain only weak bias fields).  
>
> If required, experiment with either including or excluding
> [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect)
> in the pipeline as a function of the best
> [```dwi2mask```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwi2mask.html#dwi2mask)
> outcome, and manually correct the masks if necessary (by *adding*
> regions that
> [```dwi2mask```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwi2mask.html#dwi2mask)
> fails to include).

## 1.7 Fibre Orientation Distribution estimation (multi-tissue spherical deconvolution) 

**\[standard processing\]**

When performing quantitative streamline tractography, multi-tissue
constrained spherical deconvolution should be performed using the unique
set of (average) tissue response functions obtained before. For this
tutorial, we will use the group average responses to ensure quantitative
measures are comparable across sessions *and* subjects:

```bash
for_each tp* : dwi2fod msmt_csd \
  IN/dwi_denoised_unringed_preproc_unbiased_upsampled.mif \
  ../../group_average_response_wm.txt IN/wmfod.mif \
  ../../group_average_response_gm.txt IN/gm.mif \
  ../../group_average_response_csf.txt IN/csf.mif \
  -mask IN/dwi_mask_upsampled.mif
```

> [!WARNING]
> If only a single subject is processed, the response functions will need
> to be replaced, for example by session-average tissue responses.
> However, this means that derived connectivity estimates will only be
> comparable across sessions of this subject, and **not** across other
> subjects.



## 1.8 Joint bias field correction and intensity normalisation

**\[standard processing\]**

To perform joint bias field correction and global intensity
normalisation of the multi-tissue compartment parameters,
use [mtnormalise](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise):

```bash
for_each tp* : mtnormalise \
  IN/wmfod.mif IN/wmfod_norm.mif \
  IN/gm.mif IN/gm_norm.mif \
  IN/csf.mif IN/csf_norm.mif \
  -mask IN/dwi_mask_upsampled.mif
```

If multi-tissue CSD was performed with the same single set of (three)
tissue response functions for all subjects, then the resulting output
of [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise) makes
the absolute amplitudes comparable between those subjects as well. Note
that this step is **important** in this pipeline, even if bias field
correction was applied earlier
using [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect),
since [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect) does *not* correct
for *global* intensity differences between subjects. The performance
of [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise) is
not significantly impacted by either having
run [```dwibiascorrect```](https://mrtrix.readthedocs.io/en/latest/reference/commands/dwibiascorrect.html#dwibiascorrect) before
or not. In case prior bias field correction was run in the
pipeline, [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise) will
further correct for residual intensity inhomogeneities.

> [!WARNING]
> Results from
> [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise)
> can be sensitive to masks that contain non-brain voxels. The underlying
> algorithm will attempt to drive the sum of tissue volumes to unity in
> such voxels — despite not containing brain tissue — which can result in
> erroneous bias field correction if the number of such voxels is large.  
>
> For this reason, we recommend using conservative (i.e. less spatially
> extended) masks for the
> [```mtnormalise```](https://mrtrix.readthedocs.io/en/latest/reference/commands/mtnormalise.html#mtnormalise)
> step. Unlike Step 6, where inclusion of all brain voxels was encouraged
> even at the expense of including some non-brain voxels, for bias field
> estimation the exclusion of non-brain voxels is of greater priority than
> inclusion of all brain voxels.

## 1.9 Preprocess T1-weighted data 

**\[pipeline-specific processing\]**

We will perform preprocessing of T1-weighted data by intensity
normalising the images and registering them to their respective
diffusion data. However, cross-modality registration is non-trivial due
to the different image contrasts, making it difficult for registration
algorithms to determine similarities. While there are many ways [how
this could be done](https://github.com/MRtrix3/mrtrix3/issues/2474), one
way is to leverage the tissue segmentations of the ODF images, which are
scaled to the relative intensity ranges of T1-weighted data, creating a
pseudo T1-weighted image that can be used for registration.

For intensity normalisation run:

```bash
for_each tp* : N4BiasFieldCorrection \
  -d 3 \
  -i IN/T1w.nii.gz \
  -o IN/T1w_norm.nii.gz
```
To derive a pseudo T1-weighted image from ODF data run:

```bash
for_each tp* : sh -c '
  mrconvert IN/wmfod_norm.mif IN/tmp_wm.mif -coord 3 0
  mrcalc IN/tmp_wm.mif 120 -mult IN/tmp_wm_scaled.mif
  mrcalc IN/gm_norm.mif 60 -mult IN/tmp_gm_scaled.mif
  mrcalc IN/csf_norm.mif 30 -mult IN/tmp_csf_scaled.mif

  mrcalc IN/tmp_wm_scaled.mif IN/tmp_gm_scaled.mif -add \
    IN/tmp_wm_gm_scaled.mif

  mrcalc IN/tmp_wm_gm_scaled.mif IN/tmp_csf_scaled.mif -add \
    IN/tmp_wm_gm_csf_scaled.mif

  mrhistmatch linear \
    IN/tmp_wm_gm_csf_scaled.mif \
    IN/T1w_norm.nii.gz \
    IN/T1w_pseudo.nii.gz

  rm IN/tmp_*.mif
'
```

To rigidly register T1-weighted data to the pseudeo T1-weighted image run:

```bash
for_each tp* : antsRegistrationSyNQuick.sh \
  -d 3 \
  -m IN/T1w_norm.nii.gz \
  -f IN/T1w_pseudo.nii.gz \
  -o IN/T1w_norm_ \
  -t r
```


> [!NOTE]
> While MRtrix3 supports the use of
> [unix pipes](https://mrtrix.readthedocs.io/en/latest/getting_started/command_line.html#unix-pipelines)
> for multi-step operations to avoid writing unneeded intermediate
> outputs, these pipes are not supported for batch processing within
> ```for_each```. Hence, multi-step operations are here executed within a
> subshell using temporary intermediate files, which are removed upon
> completion of each job.

> [!WARNING]
> Accurate alignment between the registered DWI and T1-weighted images is
> **critical** for this pipeline, as any residual misalignment between
> modalities will compromise the quality of the upcoming multi-modal
> inter-session registration. This, in turn, will affect downstream steps
> such as the computation of fixel-wise differences.  
>
> It is therefore essential to ensure that susceptibility-induced
> distortions have been appropriately corrected, and that good
> correspondence between diffusion and anatomical images has been
> achieved.

> [!TIP]
> For simplicity, we here transform the T1-weighted image to DWI space.
> This implies, however, that any output that was potentially derived previously from
> the T1-weighted image must also be transformed to preserve spatial
> alignment. Alternatively, one can also apply the inverse transform to
> the DWI data using mrtransform (requires conversion of the transform to
> MRtrix3 format), which will correctly reorient the gradient vectors,
> provided that the diffusion gradient table is stored in the DWI image
> header.
