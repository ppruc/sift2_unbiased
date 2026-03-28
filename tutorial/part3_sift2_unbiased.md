# PART 3 - LONGITUDINAL QUANTITATIVE STREAMLINE TRACTOGRAPHY

The following sections will walk through two distinct strategies of **unbiased SIFT2** 
tractogram density optimisation - **symmetric** and **differential** optimisation - 
both allowing the robust quantification of longitudinal structural connectivity differences. 
The optimisation procedures will either use FD or FDC maps as target fibre densities, 
depending on if rigid or non-linear registration was used.

> [!NOTE]
> To run unbiased SIFT2 optimisation an updated version of the ```tcksift2``` command
> needs to be compiled, which is [available through the MRtrix3 GitHub repository](https://github.com/MRtrix3/mrtrix3/tree/sift2diff).
> After sucessful compilation of the command, replace ```path/to/installation/...``` in the upcoming variable defintion with the relevant path on your system.

```bash
export tcksift2_unbiased="path/to/installation/mrtrix3_sift2unb/bin/tcksift2"
```

Depending on whether the unbiased within-subject template was generated using rigid or non-linear registration, 
the subsequent SIFT2 optimisation procedures will be based on either the FD or FDC metric.

If rigid registration was performed run:
```bash
export metric="fd"
```

If non-linear registration was performed run:
```bash
export metric="fdc"
```

## 3.1 SYMMETRIC OPTIMISATION

This strategy first optimises the densities of the subject-specific
tractogram so that they equally represent all analysed timepoints. This
*"unbiased quantitative tractogram"* is then separately optimised to fit the fibre
densities of each individual session.

### 3.1.1 Computation of an unbiased quantitative tractogram 

**\[pipeline-specific processing\]**

To derive a set of unbiased density weights for the subject-specific
tractogram, it is optimised to fit session-average fixel-wise fibre
density measurements. This can be achieved through SIFT2 tractogram
density optimisation.

```bash
mkdir -p template/weights

mrmath template/fixels/metrics/${metric}_tp* mean template/fixels/metrics/${metric}_mean.mif

${tcksift2_unbiased} \
  -act template/5tt.mif \
  template/tracks_10M.tck \
  template/fixels/metrics/${metric}_mean.mif \
  template/weights/tracks_10M_mean.txt \
  -out_mu template/weights/sift2_mu.txt
```

### 3.1.2 Symmetrically optimise the unbiased quantitative tractogram 

**\[pipeline-specific processing\]**

Having precomputed a set of unbiased density weights for the
subject-specific tractogram, we can now use these weights (*="factors"*) 
to initialise additional SIFT2<sub>symmetric</sub> runs, further optimising 
the densities so that they match session-specific data.

```bash
mu=$(cat template/weights/sift2_mu.txt)

for_each tp* : ${tcksift2_unbiased} \
  -act template/5tt.mif \
  template/tracks_10M.tck \
  template/fixels/metrics/${metric}_IN.mif \
  template/weights/tracks_10M_IN.txt \
  -init_factors template/weights/tracks_10M_mean.txt \
  -in_mu ${mu}
```

The output is a set of streamline weights for each session, where each
weight encodes the density contribution of the streamline to the fibre
density signal along its length.

> [!NOTE]
> The proportionality coefficient μ acts as a global scaling factor between
> the density of the reconstructed tractogram and the total fibre density across all fixels.
> Here, μ is estimated from the within-subject template and then held constant across timepoints, 
> ensuring that streamline weights remain directly comparable. 

### 3.1.3 Reconstruction of session-wise structural connectomes 

**\[pipeline-specific processing\]**

To construct edge-wise structural connectomes for each session,
streamlines are first assigned to pairs of brain regions. Edge-wise
connectivity is then computed by summarising the density weights of
streamlines assigned to pairs of regions:

```bash
mkdir connectomes

for_each tp* : tck2connectome \
  template/tracks_10M.tck \
  template/nodes.mif \
  connectomes/IN.csv \
  -tck_weights_in template/weights/tracks_10M_IN.txt
```

> [!NOTE]
> Even though the streamline assignment process is repeated here for each
> session, its outcomes will not change because both the parcellation and
> the streamline trajectories remain constant. The only thing that
> changes, are the density weights assigned to streamlines, ensuring that
> subsequent computation of edge-wise connectivity differences is
> exclusively driven by differences in streamline densities, yet not their
> assignment to parcels.
> 
> To compute the Fibre Bundle Capacity (FBC) metric, edges need to be
> scaled by the model's proportionality coefficient *mu*, which relates
> the total length of reconstructed streamlines to the sum of measured
> white matter signal. It is specifically this global scaling by *mu* that
> appropriately normalises connection-densities across sessions (and/or
> subjects), making connectivity estimates sensitive to biological
> differences between sessions, yet insensitive to the parameters of
> tractogram reconstruction (provided the underlying FODs share a common
> unique set of response functions, see. Step 1.4).

The session-wise FBC is computed as follows:

```bash
python3 - << 'EOF'
import numpy as np
import pandas as pd
from glob import glob

sift2_mu = np.loadtxt(f"template/weights/sift2_mu.txt")

for tp in glob("tp*"):
    connectome = pd.read_csv(f"connectomes/{tp}.csv", header=None)
    connectome_fbc = connectome * sift2_mu
    connectome_fbc.to_csv(
        f"connectomes/{tp}_fbc.csv",
        header=False,
        index=False
    )
EOF
```


### 3.1.4 Compute longitudinal connectome differences

**\[pipeline-specific processing\]**

Finally, we can compute the longitudinal difference in edge-wise FBC
across sessions, which in the case of two sessions can be computed as:

```bash
python3 - << 'EOF'
import pandas as pd

connectome_fbc_tp1 = pd.read_csv("connectomes/tp1_fbc.csv", header=None)
connectome_fbc_tp2 = pd.read_csv("connectomes/tp2_fbc.csv", header=None)

connectome_fbc_diff = connectome_fbc_tp2 - connectome_fbc_tp1
connectome_fbc_diff.to_csv(
    "connectomes/tp2_min_tp1_diff_fbc.csv",
    header=False,
    index=False
)
EOF
```

## 3.2 DIFFERENTIAL OPTIMISATION 

This strategy first optimises the densities of the subject-specific
tractogram so that they equally represent all analysed timepoints. This
*"unbiased quantitative tractogram"* is then directly optimised to fit fibre density
differences between sessions.

### 3.2.1 Optimise tractogram to fit fibre density differences

**\[pipeline-specific processing\]**

To optimise the tractogram to fit fibre-density *differences* between
sessions, we first need to compute the fixel-wise longitudinal change.
Since we want to be unbiased in respect of all timepoints, this needs to
be the difference of timepoints to the unbiased mean. 

In the case of two sessions, we can simply compute the unbiased mean, 
as well as the *half* difference between timepoints:

```bash
mrmath template/fixels/metrics/${metric}_tp* mean template/fixels/metrics/${metric}_mean.mif

mrcalc \
  template/fixels/metrics/${metric}_tp2.mif \
  template/fixels/metrics/${metric}_tp1.mif \
  -sub - | \
mrcalc \
  - 0.5 \
  -mult \
  template/fixels/metrics/${metric}_tp2_min_tp1_half.mif
```

We now can run SIFT2<sub>differential</sub>, which determines a set of
differential streamline weights that explains the measured fixel-wise
fibre density differences.

```bash
${tcksift2_unbiased} \
  -act template/5tt.mif \
  template/tracks_10M.tck \
  template/fixels/metrics/${metric}_mean.mif \
  template/weights/tracks_10M_mean.txt \
  -differential template/fixels/metrics/${metric}_tp2_min_tp1_half.mif \
  template/weights/tp2_min_tp1_half.txt \
  -out_mu template/weights/sift2_mu.txt
```

The output is a set of \"delta weights\", where each weight encodes the
contribution of a given streamline to the the underlying fibre density
differences along its length.

> [!WARNING]
> The input difference needs to be a *half* fibre density difference (the
> distance of each timepoint to the mean); providing the full difference
> may yield erroneous results due to the technical implementation of
> differential optimisation.

> [!NOTE]
> The above command executes two separate optimisation runs, one absolute
> SIFT2 and one differential SIFT2 run. First, the absolute run estimates
> streamline-wise density weights (*= "factors"*) in respect to the
> session-average fibre densities (*= "unbiased quantitative tractogram"*). The second
> differential run, then estimates the fractional change (the *="delta coefficient"*) 
> of streamline-wise density weights to explain the
> underlying fibre density differences. What is exported is the absolute
> change in streamline-wise density between session (*= "delta weight"*).

> [!NOTE]
> If more than two timepoints are analysed, more complex steps are
> necessary to follow the differential pipeline, as one no longer can just
> do a simple subtraction of two fixel data files. What is required
> instead is a first-level statistical model (akin to those used in fMRI
> analysis) modelling longitudinal change. Differential optimisation is then
> based on the outcomes of that first-level model, requiring only a single
> optimisation run. While this approach can offer substantial computational 
> advantages for multi-timepoint analyses, it is beyond the scope of this tutorial. 
> If you are interested in adopting this advanced processing stream, 
> please feel free to get in touch for further discussion.


### 3.2.2 Reconstruct longitudinal connectome differences

**\[pipeline-specific processing\]**

Now we can directly construct a differential structural connectome by
assigning streamlines to pairs of brain region and summarising their
differential weights to derive measures of edge-wise connectivity
differences.

```bash
mkdir connectomes
tck2connectome \
  template/tracks_10M.tck \
  template/nodes.mif \
  connectomes/tp2_min_tp1_half.csv \
  -tck_weights_in template/weights/tp2_min_tp1_half.txt
```

If one seeks to quantify the full longitudinal differences in between
timepoints, this half difference simply is multiplied by factor two. To
specifically compute differences in the Fibre Bundle Capacity (FBC)
metric, edges need to be additionally scaled by the model's
proportionality coefficient *mu*, which relates the total length of
reconstructed streamlines to the sum of measured white matter signal:

```bash
python3 - << 'EOF'
import numpy as np
import pandas as pd

connectome_diff_half = pd.read_csv("connectomes/tp2_min_tp1_half.csv", header=None)
sift2_mu = np.loadtxt("template/weights/sift2_mu.txt")

connectome_diff_full_fbc = connectome_diff_half * 2 * sift2_mu
connectome_diff_full_fbc.to_csv(
    "connectomes/tp2_min_tp1_full_fbc.csv",
    header=False,
    index=False
)
EOF
```

> [!NOTE]
> In symmetric optimisation, the global scaling by *mu* is crucial for the
> reliable comparison of connectivity measurements across different
> sessions (and/or subjects). In differential optimisation, connectivity
> changes are obtained by directly optimising the unbiased quantitative tractogram to
> match FDC differences, and therefore do not, in principle, require this
> scaling for robustly quantifying within-subject connectivity change.
> However, if the goal of the analysis is to compare connectivity
> differences *across individuals*, this scaling again becomes
> **absolutely crucial,** as only the scaled outputs are comparable
> between subjects (provided the underlying FODs across subjects share a
> common unique set of response functions, see. Step 1.4).


### 3.2.3 Compute of session-wise structural connectomes

**\[pipeline-specific processing\]**

If required, it is also fully feasible to also derive absolute
connectomes by adding/subtracting the half FBC differences to/from the
FBC of the within-subject template.

First, reconstruct the session-average connectome:

```bash
tck2connectome \
  template/tracks_10M.tck \
  template/nodes.mif \
  connectomes/mean.csv \
  -tck_weights_in template/weights/tracks_10M_mean.txt
```

Finally, reconstruct the individual timepoints, which in the case of two
sessions, can be performed as follows:

```bash
python3 - << 'EOF'
import numpy as np
import pandas as pd

sift2_mu = np.loadtxt("template/weights/sift2_mu.txt")

connectome_mean_fbc = pd.read_csv("connectomes/mean.csv", header=None) * sift2_mu
connectome_diff_half_fbc = (
    pd.read_csv("connectomes/tp2_min_tp1_half.csv", header=None) * sift2_mu
)

connectome_tp1_fbc = connectome_mean_fbc - connectome_diff_half_fbc
connectome_tp2_fbc = connectome_mean_fbc + connectome_diff_half_fbc

connectome_tp1_fbc.to_csv("connectomes/tp1_fbc.csv", header=False, index=False)
connectome_tp2_fbc.to_csv("connectomes/tp2_fbc.csv", header=False, index=False)
EOF
```
