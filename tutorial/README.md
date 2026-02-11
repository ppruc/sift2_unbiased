# Introduction
This tutorial outlines how to perform quantitative streamline
tractography to robustly estimate longitudinal changes in white matter
connectivity. This is facilitated by **unbiased SIFT2 optimisation**
[[Pruckner2026]](https://www.biorxiv.org/content/10.64898/2026.02.09.704742v1), which extends the original SIFT2 method
[[Smith2015]](https://www.sciencedirect.com/science/article/pii/S1053811915005972)
to enable robust longitudinal quantification of changes in
**Fiber Bundle Capacity (FBC)**
[[Smith2022]](https://apertureneuro.org/article/81056-quantitative-streamlines-tractography-methods-and-inter-subject-normalisation).

Instead of cross-sectionally reconstructing tractograms for each analysed
timepoint, the presented framework derives a single, subject-specific
**“unbiased quantitative tractogram,”** which serves as a starting point
for subsequent **"symmetric"** or **"differential"** SIFT2 optimisation,
thereby enabling robust estimation of changes in FBC.  

We here refer to a tractogram as *quantitative* if it has been (SIFT2)
density-optimised, and as *unbiased* if it has been constructed within an
unbiased session-average template, such that it is equally representative
of all timepoints.

Many of the steps are similar (or even equivalent) to those in the
[Fixel-Based Analysis (FBA)
tutorial](https://mrtrix.readthedocs.io/en/latest/fixel_based_analysis/mt_fibre_density_cross-section.html)
but have been reproduced/adapted here for completeness of content; for
clarity, steps are flagged as **"standard processing"** if they have been
reproduced from the FBA tutorial and apply more generally (e.g.
preprocessing), and as **"pipeline-specific processing"** if they are
specific to this pipeline (e.g. unbiased SIFT2 optimisation). The
commands are written as they were **run from within the directory of a
single subject with two (or more) longitudinal timepoints**, and make
extensive use of the [for_each script to simplify batch
processing](https://mrtrix.readthedocs.io/en/latest/tips_and_tricks/batch_processing_with_foreach.html#batch-processing).
This tutorial also assumes that the imaging dataset is organised with
separate directories identifying each session, containing T1-weighted
and diffusion-weighted imaging (DWI) data with [gradient table stored in
the image header](https://mrtrix.readthedocs.io/en/dev/reference/commands/mrconvert.html), e.g.:

- BIDS/derivatives/longitudinal_sift2/sub-exemplar/tp1/

  - t1w.mif

  - dwi.mif

- BIDS/derivatives/longitudinal_sift2/sub-exemplar/tp2/

  - t1w.mif

  - dwi.mif

The **first part** of the tutorial will run through the required
preprocessing steps and constrained spherical deconvolution to
derive session specific fibre orientation distribution functions. 
The **second part** demonstrates the construction of an unbiased
within-subject template, quantification fixel-wise fibre density metrics, 
as well as derivation of an unbiased quantitative tractogram. 
The **third part** of the tutorial then presents two different options for unbiased SIFT2 optimisation:

- **SIFT2<sub>symmetric</sub>,** where an unbiased quantitative tractogram is optimised to fit
  session-specific fibre-densities.

- **SIFT2<sub>differential</sub>,** where an unbiased tractogram is optimised to
  directly fit session-specific fibre-densities *differences*.

Both options can construct session-wise and differential connectomes,
and it is up to users which one may be preferable for their analysis.
That said, **differential optimisation is approximately 30% faster**
than the symmetric variant in the case of two timepoints.

For all MRtrix scripts and commands, additional information on the
command usage and available command-line options can be found by
invoking the command with the ```-help``` option.

# Prerequisites
- MRtrix3 installation, with commands present in ```PATH```
- FreeSurfer installation, with commands present in ```PATH```
- FSL installation, with commands present in ```PATH```
- ANTs installation, with commands present in ```PATH```
- MRtrix3 installation (separate build) with the [updated version of the tcksift2 command](https://github.com/MRtrix3/mrtrix3/tree/sift2diff)
- MRtrix3 installation (separate build) with the [updated version of the version of the fixelcorrespondence command](https://github.com/MRtrix3/mrtrix3/tree/fixelcorrespondence)
- python3 installation, including pandas and numpy
- Recommended: [ACPC Detect](https://www.nitrc.org/projects/art/) installation

# Table of Contents

[**PART 1: Pre-processing and Constrained Spherical Deconvolution**](part1_preprocessing_csd.md)

- 1.1	Denoising and unringing
- 1.2	Motion and distortion correction
- 1.3 Bias field correction
- 1.4 Response function estimation
- 1.4.1 Computing session-average tissue response functions
- 1.4.2 Computing cohort-average tissue response functions
- 1.5 Upsampling DWI images
- 1.6. Compute upsampled brain mask images
- 1.7 Fibre Orientation Distribution estimation (multi-tissue spherical deconvolution)
- 1.8 Joint bias field correction and intensity normalisation	
- 1.9 Preprocess T1-weighted data

[**PART 2: Generation of Within-Subject Templates, Fixels and Tractography**](part2_template_tractogram.md)
- 2.1 Generate unbiased FOD and T1-weighted within-subject templates
- 2.2 Derivation of relevant T1-weighted outputs
  - 2.2.1 Reconstruction of the T1-weighted within-subject template
  - 2.2.2 Segmentation of different tissue types
  - 2.2.3 Derivation of a cortical and subcortical brain parcellation
- 2.3 Fixels and fixel-based quantitive metrics
  - 2.3.1 Compute a white matter template analysis fixel mask
  - 2.3.2 Transform FOD images to template space
  - 2.3.3 Segment FOD images to estimate fixels and their apparent fibre density
  - 2.3.4 Reorient fixels
  - 2.3.5 Assign subject fixels to template fixels
  - 2.3.6 Compute the fibre cross-section (FC) metric
  - 2.3.7 Compute a combined measure of fibre density and cross-section (FDC)
- 2.4 Perform whole-brain fibre tractography on the within-subject template

[**PART 3: Longitudinal Quantitative Streamline Tractography**](part3_sift2_unbiased.md)
- 3.1 Symmetric optimisation
  - 3.1.1 Computation of an unbiased tractogram
  - 3.1.2 Symmetrically optimise the unbiased tractogram
  - 3.1.3 Reconstruction of session-wise structural connectomes
  - 3.1.4 Compute longitudinal connectome differences
- 3.2 Differential optimisation
  - 3.2.1 Optimise tractogram to fit fibre density differences
  - 3.2.2 Reconstruct longitudinal connectome differences
  - 3.2.3 Compute of session-wise structural connectomes

[**APPENDIX: Integration of Robust Longitudinal Grey and White Matter Reconstruction**](part4_appendix.md)
- 4.1 Within-subject template generation
- 4.2 Longitudinal FreeSurfer
  - 4.2.1 Reconstruction of session-wise T1-weighted images
  - 4.2.2 Base template reconstruction
  - 4.2.3. Longitudinal timepoint reconstruction

