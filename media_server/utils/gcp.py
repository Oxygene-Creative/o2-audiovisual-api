from google.cloud import storage
from google.oauth2 import service_account
import os

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