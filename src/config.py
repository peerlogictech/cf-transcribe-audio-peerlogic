import os

from dotenv import load_dotenv

# ensure environment variables are loaded
load_dotenv()


PROJECT_ID = os.environ["PROJECT_ID"]
BUCKET_OUTPUT_AUDIO_PCM_ENCODED = os.environ["BUCKET_OUTPUT_AUDIO_PCM_ENCODED"]
BUCKET_OUTPUT_RAW_EXTRACT = os.environ["BUCKET_OUTPUT_RAW_EXTRACT"]
