import matplotlib.pyplot as plt
import os
import numpy as np

def extract_differential_weights(phantom_path,sift,tcks,reg_basis_abs,reg_fn_abs,reg_strength_abs,reg_fn_diff,reg_basis_diff,reg_strength_diff,extract=None,histogram=False,xlim=None,save_png=False,no_labels=False):
    
    if extract == "weights":
        file = "sift2diff_weights.txt"
    elif extract == "coeffs":
        file = "sift2diff_coeffs.txt"
    else:
        print("ERROR: 'extract' must be 'weights' or 'coeffs'")
        
    file_path = f"{phantom_path}/simulations/{sift}/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/reg_fn_diff_{reg_fn_diff}/reg_basis_diff_{reg_basis_diff}/reg_diff_{reg_strength_diff}/{file}"

    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Ensure the second line exists and is processed correctly
    if len(lines) > 1:
        second_line = lines[1]
        data = np.array(list(map(float, second_line.split()))) 
 
    if histogram:
        plt.hist(data, bins=100, edgecolor='black')
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if no_labels:
            plt.xlabel('',fontsize=12)
            plt.ylabel('',fontsize=12)
            plt.title('',fontsize=12)
        else:
            plt.xlabel('Values',fontsize=12)
            plt.ylabel('Frequency',fontsize=12)
            plt.title(f"Differential SIFT2 {extract} reg_basis_abs {reg_basis_abs} reg_strength_abs {reg_strength_abs} reg_basis_diff {reg_basis_diff} reg_strength_diff {reg_strength_diff}",fontsize=12)
        if xlim:
            plt.xlim(xlim)
            
        if save_png != None:
            output_path = f"{save_png}/{extract}"
            os.makedirs(output_path,exist_ok=True)
            file = f"reg_strength_diff_{reg_strength_diff}.png"
            png = os.path.join(output_path,file)
            plt.savefig(png, dpi=300, bbox_inches='tight')
            print(f"plotting weight distribution of {file_path}")
            plt.show()
        
        print(f"plotting weight distribution of {file_path}")
        plt.show()
    
    return data
