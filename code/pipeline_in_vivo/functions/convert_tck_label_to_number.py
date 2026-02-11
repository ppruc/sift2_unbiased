import sys
import os

sys.path.append(os.path.abspath('/path/to/functions')) # can be found in git repository (./code/in_vivo/functions)

def convert_tck_label_to_number(label: str) -> int:
    """
    Convert streamline count labels like '100k', '2.5M', or '250000' to an integer count.
    Returns an int suitable for MRtrix's `-select`.
    """
    if label is None:
        raise ValueError("Label is None.")

    s = str(label).strip()
    if not s:
        raise ValueError("Empty label string.")

    # Handle suffixes (case-insensitive)
    last = s[-1].lower()
    if last in ('k', 'm'):
        try:
            num = float(s[:-1])
        except ValueError:
            raise ValueError(f"Invalid numeric part in label: {label!r}")
        mult = 1_000 if last == 'k' else 1_000_000
        count = int(round(num * mult))
    else:
        # No suffix → assume raw count
        try:
            # Allow floats like "250000.0" but coerce to int safely
            num = float(s)
        except ValueError:
            raise ValueError(f"Unknown/invalid label format: {label!r}")
        if num < 0:
            raise ValueError(f"Negative streamline count: {label!r}")
        count = int(round(num))

    if count <= 0:
        raise ValueError(f"Non-positive streamline count after conversion: {label!r}")

    return count
