import sys
import os
import pandas as pd

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)
from run_command import run_command
from get_sessions import get_sessions

def sift2_results(derivatives_dir, subs, ntcks, params_cross, params_temp, params_sym, params_diff):

    reg_basis_abs_cross, reg_fn_abs_cross, reg_strength_abs_cross = params_cross
    reg_basis_abs_temp, reg_fn_abs_temp, reg_strength_abs_temp = params_temp
    reg_basis_abs_sym, reg_fn_abs_sym, reg_strength_abs_sym = params_sym
    reg_basis_diff, reg_fn_diff, reg_strength_diff = params_diff

    os.chdir(derivatives_dir)
    try:
        os.rmdir(f"{derivatives_dir}/sift2_results/{ntcks}/")
    except:
        pass
    os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_cross/convergence", exist_ok=True)
    os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_template/convergence", exist_ok=True)
    os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_symmetric/convergence", exist_ok=True)
    os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/convergence", exist_ok=True)


    for sub in subs:
        for ses in get_sessions(derivatives_dir, sub):
            run_command(f"cp {derivatives_dir}/{sub}/ses-average/weights/sift2_cross/{ses}/reg_basis_cross_{reg_basis_abs_cross}/reg_fn_cross_{reg_fn_abs_cross}/reg_strength_cross_{reg_strength_abs_cross}/algorithm_{ntcks}_convergence.txt {derivatives_dir}/sift2_results/{ntcks}//sift2_cross/convergence/{sub}_{ses}.csv")
            
            run_command(f"cp {derivatives_dir}/{sub}/ses-average/weights/sift2_symmetric/{ses}/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_sym_{reg_basis_abs_sym}/reg_fn_sym_{reg_fn_abs_sym}/reg_strength_sym_{reg_strength_abs_sym}/algorithm_{ntcks}_convergence.txt {derivatives_dir}/sift2_results/{ntcks}//sift2_symmetric/convergence/{sub}_{ses}.csv")
        
        run_command(f"cp {derivatives_dir}/{sub}/ses-average/weights/sift2_template/ses-average/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/algorithm_{ntcks}_convergence.txt {derivatives_dir}/sift2_results/{ntcks}//sift2_template/convergence/{sub}.csv")
        
        run_command(f"cp {derivatives_dir}/{sub}/ses-average/weights/sift2_differential/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_diff_{reg_basis_diff}/reg_fn_diff_{reg_fn_diff}/reg_strength_diff_{reg_strength_diff}/algorithm_{ntcks}_convergence.txt {derivatives_dir}/sift2_results/{ntcks}//sift2_differential/convergence/{sub}.csv")



    for sub in subs:
        for idx,ses in enumerate(get_sessions(derivatives_dir, sub)):
        
            # Cross Sectional: no sift
            os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_none/fbc_absolute/",exist_ok=True)
            run_command(f"cp"
                f" {derivatives_dir}/{sub}/ses-average/weights/sift2_none/{ses}/connectome_{ntcks}_fbc.csv"
                f" {derivatives_dir}/sift2_results/{ntcks}//sift2_none/fbc_absolute/{sub}_ses-0{idx+1}_connectome_fbc.csv"
                )
        
            # Cross Sectional: sift
            os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_cross/fbc_absolute/",exist_ok=True)
            run_command(f"cp"
                f" {derivatives_dir}/{sub}/ses-average/weights/sift2_cross/{ses}/reg_basis_cross_{reg_basis_abs_cross}/reg_fn_cross_{reg_fn_abs_cross}/reg_strength_cross_{reg_strength_abs_cross}/connectome_{ntcks}_fbc.csv"
                f" {derivatives_dir}/sift2_results/{ntcks}//sift2_cross/fbc_absolute/{sub}_ses-0{idx+1}_connectome_fbc.csv"
                )
       
            # Unbiased: sym
            os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_symmetric/fbc_absolute/",exist_ok=True)
            run_command(f"cp"
                f" {derivatives_dir}/{sub}/ses-average/weights/sift2_symmetric/{ses}/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_sym_{reg_basis_abs_sym}/reg_fn_sym_{reg_fn_abs_sym}/reg_strength_sym_{reg_strength_abs_sym}/connectome_{ntcks}_fbc.csv"
                f" {derivatives_dir}/sift2_results/{ntcks}//sift2_symmetric/fbc_absolute/{sub}_ses-0{idx+1}_connectome_fbc.csv"
                    )
            
            # Unbiased: Differential
            os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_differential/fbc_absolute/",exist_ok=True)
        
            run_command(f"cp"
                f" {derivatives_dir}/{sub}/ses-average/weights/sift2_differential/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_diff_{reg_basis_diff}/reg_fn_diff_{reg_fn_diff}/reg_strength_diff_{reg_strength_diff}/connectome_{ntcks}_tp{idx+1}_fbc.csv"
                f" {derivatives_dir}/sift2_results/{ntcks}//sift2_differential/fbc_absolute/{sub}_ses-0{idx+1}_connectome_fbc.csv"
                )
        
        
    for sub in subs:
        sessions = get_sessions(derivatives_dir,sub)
        ses1, ses2 = sessions
        
        # Cross Sectional: no sift
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_none/fbc_differences/",exist_ok=True)
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_none/fbc_differences_fract", exist_ok=True)
        connectome_tp1 = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_none/{ses1}/connectome_{ntcks}_fbc.csv", header=None)
        connectome_tp2 = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_none/{ses2}/connectome_{ntcks}_fbc.csv", header=None)
        connectome_diff = connectome_tp2 - connectome_tp1
        connectome_diff_fract = connectome_diff/connectome_tp1.replace(0, pd.NA)
        connectome_diff.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_none/fbc_differences/{sub}_connectome_diff_fbc.csv", index=False, header=False)
        connectome_diff_fract.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_none/fbc_differences_fract/{sub}_connectome_diff_fbc.csv", index=False, header=False)

        # Cross Sectional: sift
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_cross/fbc_differences/",exist_ok=True)
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_cross/fbc_differences_fract", exist_ok=True)
        connectome_tp1 = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_cross/{ses1}/reg_basis_cross_{reg_basis_abs_cross}/reg_fn_cross_{reg_fn_abs_cross}/reg_strength_cross_{reg_strength_abs_cross}/connectome_{ntcks}_fbc.csv", header=None)
        connectome_tp2 = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_cross/{ses2}/reg_basis_cross_{reg_basis_abs_cross}/reg_fn_cross_{reg_fn_abs_cross}/reg_strength_cross_{reg_strength_abs_cross}/connectome_{ntcks}_fbc.csv", header=None)
        connectome_diff = connectome_tp2 - connectome_tp1
        connectome_diff_fract = connectome_diff/connectome_tp1.replace(0, pd.NA)
        connectome_diff.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_cross/fbc_differences/{sub}_connectome_diff_fbc.csv", index=False, header=False)
        connectome_diff_fract.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_cross/fbc_differences_fract/{sub}_connectome_diff_fbc.csv", index=False, header=False)

        # Unbiased: sym
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_symmetric/fbc_differences/",exist_ok=True)
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_symmetric/fbc_differences_fract", exist_ok=True)
        connectome_tp1 = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_symmetric/{ses1}/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_sym_{reg_basis_abs_sym}/reg_fn_sym_{reg_fn_abs_sym}/reg_strength_sym_{reg_strength_abs_sym}/connectome_{ntcks}_fbc.csv", header=None)
        connectome_tp2 = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_symmetric/{ses2}/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_sym_{reg_basis_abs_sym}/reg_fn_sym_{reg_fn_abs_sym}/reg_strength_sym_{reg_strength_abs_sym}/connectome_{ntcks}_fbc.csv", header=None)
        connectome_diff = connectome_tp2 - connectome_tp1
        connectome_diff_fract = connectome_diff/connectome_tp1.replace(0, pd.NA)
        connectome_diff.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_symmetric/fbc_differences/{sub}_connectome_diff_fbc.csv", index=False, header=False)
        connectome_diff_fract.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}//sift2_symmetric/fbc_differences_fract/{sub}_connectome_diff_fbc.csv", index=False, header=False)

        # Unbiased: Differential
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/fbc_differences",exist_ok=True)
        os.makedirs(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/fbc_differences_fract", exist_ok=True)
        connectome_tp1 = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_differential/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_diff_{reg_basis_diff}/reg_fn_diff_{reg_fn_diff}/reg_strength_diff_{reg_strength_diff}/connectome_{ntcks}_tp1_fbc.csv", header=None)
        connectome_diff = pd.read_csv(f"{derivatives_dir}/{sub}/ses-average/weights/sift2_differential/reg_basis_temp_{reg_basis_abs_temp}/reg_fn_temp_{reg_fn_abs_temp}/reg_strength_temp_{reg_strength_abs_temp}/reg_basis_diff_{reg_basis_diff}/reg_fn_diff_{reg_fn_diff}/reg_strength_diff_{reg_strength_diff}/connectome_{ntcks}_diff_full_fbc.csv", header=None)
        connectome_diff_fract = connectome_diff/connectome_tp1.replace(0, pd.NA)
        connectome_diff.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/fbc_differences/{sub}_connectome_diff_fbc.csv", index=False, header=False)
        connectome_diff_fract.iloc[:85, :85].to_csv(f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/fbc_differences_fract/{sub}_connectome_diff_fbc.csv", index=False, header=False)

    # Create files.txt for fbc_absolute directories
    for folder in [
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_none/fbc_absolute/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_cross/fbc_absolute/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_symmetric/fbc_absolute/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/fbc_absolute/"
    ]:
        files = os.listdir(folder)
        with open(os.path.join(folder, "files.txt"), "w") as f:
            for filename in files:
                if filename != "files.txt":
                    f.write(filename + "\n")

    # Create files.txt for fbc_differences directories
    for folder in [
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_none/fbc_differences/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_cross/fbc_differences/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_symmetric/fbc_differences/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/fbc_differences"
    ]:
        files = os.listdir(folder)
        with open(os.path.join(folder, "files.txt"), "w") as f:
            for filename in files:
                if filename != "files.txt":
                    f.write(filename + "\n")

    # Aggregate fbc_differences per group (mean and std)
    import numpy as np

    for folder in [
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_none/fbc_differences/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_cross/fbc_differences/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_symmetric/fbc_differences/",
        f"{derivatives_dir}/sift2_results/{ntcks}/sift2_differential/fbc_differences/"
    ]:
        out_folder = os.path.join(folder, "aggregated")
        os.makedirs(out_folder, exist_ok=True)
        files = [f for f in os.listdir(folder) if f.endswith(".csv") and not f.startswith("mean") and not f.startswith("std")]
        matrices = []

        for fname in files:
            df = pd.read_csv(os.path.join(folder, fname), header=None)
            matrices.append(df.values)

        if matrices:
            stacked = np.stack(matrices, axis=0)  # shape: (subjects, N, N)
            mean_mat = np.mean(stacked, axis=0)
            median_mat = np.median(stacked, axis=0)
            std_mat = np.std(stacked, axis=0)


            pd.DataFrame(mean_mat).to_csv(os.path.join(out_folder, "mean_connectome_diff_fbc.csv"), index=False, header=False)
            pd.DataFrame(median_mat).to_csv(os.path.join(out_folder, "median_connectome_diff_fbc.csv"), index=False, header=False)
            pd.DataFrame(std_mat).to_csv(os.path.join(out_folder, "std_connectome_diff_fbc.csv"), index=False, header=False)
