import os

def subfolder_check(subfolder_path: str):
  if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)
        
def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} has been deleted successfully.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except PermissionError:
        print(f"Permission denied: Unable to delete {file_path}.")
    except Exception as e:
        print(f"Error occurred while deleting {file_path}: {e}")
        
def extract_file_name(file_path):
    file_name = os.path.basename(file_path)
    return file_name

def calc_file_size(file_path) -> float:
    try:
        # Get file size in bytes
        file_size_bytes = os.path.getsize(file_path)

        # Convert bytes to megabytes
        file_size_mb = file_size_bytes / (1024 * 1024)

        return file_size_mb
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    