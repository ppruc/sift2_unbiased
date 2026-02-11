import pandas as pd 

def define_study(results_dir,dataset):
    
    if dataset == "HCP_Scan_rescan":
    
        data_dir = f"{results_dir}/data/{dataset}"
    
        subs = [
            "sub-917255", "sub-877168", "sub-861456", "sub-859671", "sub-783462",
            "sub-660951", "sub-627549", "sub-601127", "sub-599671", "sub-562345",
            "sub-433839", "sub-341834", "sub-287248", "sub-250427", "sub-204521",
            "sub-200614", "sub-200109", "sub-195041", "sub-194140", "sub-192439",
            "sub-187547", "sub-185442", "sub-177746", "sub-175439", "sub-172332",
            "sub-169343", "sub-158035", "sub-151526", "sub-149741", "sub-149337",
            "sub-146129", "sub-144226", "sub-143325", "sub-139839", "sub-137128",
            "sub-135528", "sub-130518", "sub-125525", "sub-122317", "sub-115320",
            "sub-114823", "sub-111312", "sub-105923", "sub-103818"
        ]

        # fs default
        fs_default_path = f"{results_dir}/code/dependencies/fs_default.txt"

        # Read the file, skipping the comment lines and using whitespace as delimiter
        labels = pd.read_csv(fs_default_path, comment='#', delim_whitespace=True, header=None,
                            names=['ID', 'Code', 'Description', 'R', 'G', 'B', 'A'])
        
        labels = labels["Description"][1:86]
        
    elif dataset == "Developing_Children":
    
        data_dir = f"{results_dir}/data/{dataset}"
    
        subs = [
            "sub-cIVs001", "sub-cIVs005", "sub-cIVs006", "sub-cIVs007", "sub-cIVs012",
            "sub-cIVs013", "sub-cIVs017", "sub-cIVs018", "sub-cIVs024", "sub-cIVs025",
            "sub-cIVs026", "sub-cIVs029", "sub-cIVs030", "sub-cIVs032", "sub-cIVs036",
            "sub-cIVs037", "sub-cIVs038", "sub-cIVs040", "sub-cIVs043", "sub-cIVs044",
            "sub-cIVs045", "sub-cIVs051", "sub-cIVs053", "sub-cIVs054", "sub-cIVs055",
            "sub-cIVs056", "sub-cIVs057", "sub-cIVs067", "sub-cIVs070", "sub-cIVs075",
            "sub-cIVs077", "sub-cIVs078", "sub-cIVs081", "sub-cIVs082", "sub-cIVs085"
        ]


        # fs default
        fs_default_path = f"{results_dir}/code/dependencies/fs_default.txt"

        # Read the file, skipping the comment lines and using whitespace as delimiter
        labels = pd.read_csv(fs_default_path, comment='#', delim_whitespace=True, header=None,
                            names=['ID', 'Code', 'Description', 'R', 'G', 'B', 'A'])
        
        labels = labels["Description"][1:86]
        
    elif dataset == "Templobe_Surgery":
    
        data_dir = f"{results_dir}/data/{dataset}"

        subs = [
            "sub-Epat03",  "sub-Epat09",  "sub-apat101", "sub-apat102", "sub-apat103",
            "sub-apat104", "sub-apat109", "sub-apat110", "sub-apat113", "sub-apat116",
            "sub-apat118", "sub-apat125", "sub-pat02",   "sub-pat04",   "sub-pat05",
            "sub-pat06",   "sub-pat07",   "sub-pat08",   "sub-pat09",   "sub-pat102",
            "sub-pat103",  "sub-pat104",  "sub-pat105",  "sub-pat106",  "sub-pat108",
            "sub-pat11",   "sub-pat110",  "sub-pat111",  "sub-pat112",  "sub-pat113",
            "sub-pat114",  "sub-pat13",   "sub-pat14",   "sub-pat15",   "sub-pat16",
            "sub-pat18",   "sub-pat19",   "sub-pat20",   "sub-pat21",   "sub-pat22",
            "sub-pat23",   "sub-pat24",   "sub-pat25",   "sub-pat26",   "sub-pat27",
            "sub-pat30",   "sub-pat31",   "sub-pat32",   "sub-pat34",   "sub-pat36",
            "sub-pat37",   "sub-pat38",   "sub-pat39"
            ]
        
         # fs default
        fs_default_path = f"{results_dir}/code/dependencies/fs_default_ipsi_contra_lut.txt"
   
        # Read the file, skipping the comment lines and using whitespace as delimiter
        labels = pd.read_csv(fs_default_path, comment='#', delim_whitespace=True, header=None,
                                names=['ID', 'Code', 'Description', 'R', 'G', 'B', 'A'])


    return data_dir, subs, labels
