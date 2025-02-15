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