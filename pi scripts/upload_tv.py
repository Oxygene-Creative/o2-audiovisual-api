from app.core.gcp import upload
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
import time

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

RECORDINGS_LOCAL_FOLDER = "/var/lib/tvheadend/recordings"

def upload_video_gcp():
    
    return

def start_video_analysis():
    return
