from google.cloud import storage
from google.oauth2 import service_account
import os
from utils.files import subfolder_check
from dotenv import load_dotenv
load_dotenv()

credentials_dict = {
    'type': 'service_account',
    'client_id': os.environ['GCP_CLIENT_ID'],
    'client_email': os.environ['GCP_CLIENT_EMAIL'],
    'private_key_id': os.environ['GCP_PRIVATE_KEY_ID'],
    'private_key': os.environ['GCP_PRIVATE_KEY'],
    "token_uri": "https://oauth2.googleapis.com/token",
}

credentials = service_account.Credentials.from_service_account_info(
    credentials_dict
)

def upload(bucket_name, source, destination_blob_name):
    storage_client = storage.Client(credentials = credentials, project=os.environ['GCP_PROJECT_ID'])
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source)
    return blob.public_url


def download_file(bucket_name, source_blob_name, destination_file_name):
    storage_client = storage.Client(credentials = credentials, project=os.environ['GCP_PROJECT_ID'])
    bucket = storage_client.bucket(bucket_name)
    
    """Downloads a blob from the bucket."""
    blob = bucket.blob(source_blob_name)

    # Determine the subfolder path from the target file path
    subfolder_path = os.path.dirname(destination_file_name)

    # Create the subfolder if it doesn't exist
    subfolder_check(subfolder_path)
    
    blob.download_to_filename(destination_file_name)
    print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")
    
def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client(credentials = credentials, project=os.environ['GCP_PROJECT_ID'])

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    generation_match_precondition = None

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to delete is aborted if the object's
    # generation number does not match your precondition.
    blob.reload()  # Fetch blob metadata to use in generation_match_precondition.
    generation_match_precondition = blob.generation

    blob.delete(if_generation_match=generation_match_precondition)

    print(f"Blob {blob_name} deleted.")