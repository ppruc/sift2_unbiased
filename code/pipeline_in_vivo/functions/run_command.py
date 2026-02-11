import os
import subprocess

def run_command(command, log_path=None):
    try:
        if log_path is not None:
            # Ensure the directory exists; if not, create it
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            # Open the log file for writing at the specified path
            with open(log_path, "w") as log_file:
                # Run the command and redirect stdout and stderr to the log file
                result = subprocess.run(
                    command,
                    shell=True,
                    stdout=log_file,  # Write stdout to the file
                    stderr=subprocess.STDOUT  # Redirect stderr to stdout
                )
        else:
            # Run the command without capturing output
            subprocess.run(command, shell=True)
    except Exception as e:
        print(f"Command '{command}' failed with error: {e}")
