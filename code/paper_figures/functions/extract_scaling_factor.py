import re

def extract_scaling_factor(filename):
    """
    Reads the file at 'filename' and extracts the numerical value 
    from the line containing:
    "Constant A scaling regularisation term to match data term is X"
    where X is a number.
    """
    pattern = r"Constant A scaling regularisation term to match data term is ([+-]?\d*\.?\d+)"
    
    with open(filename, 'r') as file:
        text = file.read()
    
    match = re.search(pattern, text)
    if match:
        # Convert the captured number to float
        try:
            value = float(match.group(1))
        except ValueError:
            value = match.group(1)  # Return as string if conversion fails
        return value
    else:
        return None

