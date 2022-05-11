import os

from dotenv import load_dotenv

# ensure environment variables are loaded
load_dotenv()


PROJECT_ID = os.getenv("PROJECT_ID")
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER")
BUCKET_OUTPUT_AUDIO_PCM_ENCODED = os.getenv("BUCKET_OUTPUT_AUDIO_PCM_ENCODED")
BUCKET_OUTPUT_RAW_EXTRACT = os.getenv("BUCKET_OUTPUT_RAW_EXTRACT")
