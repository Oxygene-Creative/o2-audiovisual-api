from app.core.graphql import get_configs
from dotenv import load_dotenv
import os

def setup_env():
    configs = get_configs()
    # set up all configs
    for config in configs:
        key = config.get("key")
        value = config.get("value")
        if key and value:
            os.environ[key] = value
       

