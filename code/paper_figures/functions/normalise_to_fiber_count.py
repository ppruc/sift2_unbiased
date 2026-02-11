import sys
import os

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from sum_upper_triangle import sum_upper_triangle

def normalise_to_fiber_count(df,fiber_count):
        density = sum_upper_triangle(df)
        normalisation_factor = fiber_count/density
        return normalisation_factor