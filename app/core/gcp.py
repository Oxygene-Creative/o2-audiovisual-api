from google.cloud import storage
from google.oauth2 import service_account
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class GCSUtil:
    def __init__(self, bucket_name, credentials_dict=None):
        self.bucket_name = bucket_name
        if credentials_dict:
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            self.client = storage.Client(credentials=credentials, 
                                      project=credentials_dict.get('project_id'))
        else:
            self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def upload_file(self, file_path, destination_blob_name):
        """Uploads a file to the bucket."""
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        print(f"File {file_path} uploaded to {destination_blob_name}.")

    def upload_from_memory(self, file_content, destination_blob_name):
        """Uploads file content from memory to the bucket."""
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(file_content)
        print(f"File content uploaded to {destination_blob_name}.")

    def upload_multiple_files(self, file_paths, destination_blob_names):
        """Uploads multiple files to the bucket concurrently."""
        def upload_single(file_path, blob_name):
            try:
                self.upload_file(file_path, blob_name)
                return f"Successfully uploaded {file_path} to {blob_name}"
            except Exception as e:
                return f"Failed to upload {file_path}: {str(e)}"

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_single, fp, bn) 
                      for fp, bn in zip(file_paths, destination_blob_names)]
            for future in as_completed(futures):
                print(future.result())

    def upload_multiple_from_memory(self, file_contents, destination_blob_names):
        """Uploads multiple file contents from memory to the bucket concurrently."""
        def upload_single(content, blob_name):
            try:
                self.upload_from_memory(content, blob_name)
                return f"Successfully uploaded content to {blob_name}"
            except Exception as e:
                return f"Failed to upload to {blob_name}: {str(e)}"

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_single, content, bn) 
                      for content, bn in zip(file_contents, destination_blob_names)]
            for future in as_completed(futures):
                print(future.result())

    def download_file(self, source_blob_name, destination_file_name):
        """Downloads a blob from the bucket."""
        blob = self.bucket.blob(source_blob_name)
        
        # Determine the subfolder path from the target file path
        subfolder_path = os.path.dirname(destination_file_name)

        # Create the subfolder if it doesn't exist
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
        
        blob.download_to_filename(destination_file_name)
        print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")
    
    def download_as_string(self, blob_name):
        """Downloads a blob's contents as a string."""
        blob = self.bucket.blob(blob_name)
        return blob.download_as_string().decode("utf-8")

    def delete_file(self, blob_name):
        """Deletes a blob from the bucket."""
        blob = self.bucket.blob(blob_name)
        blob.delete()
        print(f"Blob {blob_name} deleted.")

    def list_files(self, prefix=None):
        """Lists all the blobs in the bucket with the given prefix."""
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        return [blob.name for blob in blobs]
    
    
# Initialize GCSUtil
credentials_dict = {
    'type': 'service_account',
    'client_id': os.environ['GCP_CLIENT_ID'],
    'client_email': os.environ['GCP_CLIENT_EMAIL'],
    'private_key_id': os.environ['GCP_PRIVATE_KEY_ID'],
    'private_key': os.environ['GCP_PRIVATE_KEY'],
    'token_uri': 'https://oauth2.googleapis.com/token',
    'project_id': os.environ['GCP_PROJECT_ID']
}


