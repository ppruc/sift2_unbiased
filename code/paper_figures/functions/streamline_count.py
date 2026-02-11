import nibabel as nib

def streamline_count(tck_path):
    tcks = nib.streamlines.load(tck_path)

    # get the number of streamlines
    n_streamlines = len(tcks.streamlines)
    
    return n_streamlines