import matplotlib.pyplot as plt
import os

def extract_absolute_weights(phantom_path,tcks,reg_basis_abs,reg_fn_abs,reg_strength_abs,extract=None,histogram=False,xlim=None,save_png=None,no_labels=False):
    
    if extract == "weights":
        file = f"sift2_weights_tp1.txt"
    elif extract == "coeffs":
        file = f"sift2_coeffs_tp1.txt"
    else:
        print("ERROR: 'extract' must be 'weights' or 'coeffs'")
    file_path = f"{phantom_path}/simulations/sift2_cross/{tcks}/reg_basis_abs_{reg_basis_abs}/reg_fn_abs_{reg_fn_abs}/reg_abs_{reg_strength_abs}/{file}"

    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Ensure the second line exists and is processed correctly
    if len(lines) > 1:
        second_line = lines[1]
        data = list(map(float, second_line.split()))  
    
    if histogram:
        plt.hist(data, bins=100, edgecolor='black')
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if no_labels:
            plt.xlabel('',fontsize=12)
            plt.ylabel('',fontsize=12)
            plt.title(f'', fontsize=12)
        else:
            plt.xlabel('Values',fontsize=12)
            plt.ylabel('Frequency',fontsize=12)
            plt.title(f'Absolute SIFT2 {extract} reg_basis {reg_basis_abs} reg_strength {reg_strength_abs}', fontsize=12)

        if xlim:
            plt.xlim(xlim)
    
        if save_png != None:
            output_path = f"{save_png}/{extract}"
            os.makedirs(output_path,exist_ok=True)
            file = f"reg_strength_abs_{reg_strength_abs}.png"
            png = os.path.join(output_path,file)
            plt.savefig(png, dpi=300, bbox_inches='tight')
        print(f"plotting weight distribution of {file_path}")
        plt.show()
    
    return data
    
 
