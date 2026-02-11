import pandas as pd
import sys
import os

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))
from extract_scaling_factor import extract_scaling_factor

def extract_differential_costs(phantom_path,tcks,reg_basis_abs,reg_fn_abs,reg_strength_abs,reg_fn_diff,reg_basis_diff,reg_strengths_diff):

    """
    Extract data and regularisation costs from algorithm convergence CSV files.

    Parameters:
    - phantom_path (str):  path/to/phantom/ 
    - tcks (str): track folder name, e.g. "tcks_template" or "tcks"
    - reg_basis_abs: "streamline", "fixel", "group"
    - reg_strenghts_abs: scalar with strenghts 
    - reg_basis_diff: "streamline", "fixel", "group"
    - reg_strenghts_diff: vector with strenghts

    Returns:
    - pd.DataFrame: DataFrame containing cost_data and cost_reg_term for each reg_strength_abs.
    """
        
    df = pd.DataFrame(columns=["cost_data", "cost_reg_term"])
    
    base_path = f"{phantom_path}/simulations/sift2_differential/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/"

    for strength in reg_strengths_diff:
        path = f"{base_path}/reg_diff_{strength}/algorithm_convergence.csv"
        scaling_factor_A = extract_scaling_factor(f"{phantom_path}/simulations/sift2_template/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/sift2_log.txt")
        try:
            tmp_df = pd.read_csv(path)
            cost_data = float(tmp_df["Cost_data"].iloc[-1])
            cost_reg = float(tmp_df["Cost_reg"].iloc[-1])
            cost_reg_term = (cost_reg / scaling_factor_A) / strength
            df.loc[strength, "cost_data"] = cost_data
            df.loc[strength, "cost_reg_term"] = cost_reg_term
            print(path)
            print(f"cost_data: {cost_data}")
            print(f"cost_reg: {cost_reg}")
            print(f"cost_reg_term: {cost_reg_term}")

        except FileNotFoundError:
            print(f"File not found: {path}")
        except KeyError as e:
            print(f"KeyError: {e} in file {path}")
        
        print(f"extracting cost from {path}")


    print(f"scaling Factor A: {scaling_factor_A}")

    return df
