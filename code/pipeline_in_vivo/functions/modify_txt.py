import numpy as np

def modify_txt(arr, switch_x_for_y):
    # Create a mapping dictionary from each x to its corresponding y
    mapping = {x: y for x, y in switch_x_for_y}
    
    # Create a vectorized function that replaces an element with its mapping if available,
    # otherwise returns the element unchanged.
    vectorized_map = np.vectorize(lambda v: mapping.get(v, v))
    
    # Apply the vectorized function to the entire array in one pass
    return vectorized_map(arr)
