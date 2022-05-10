import logging
import os
import tempfile
import wave
from typing import Union

from google.cloud import storage

from config import PROJECT_ID

storage_client = storage.Client(project=PROJECT_ID)

# Get an instance of a logger
log = logging.getLogger(__name__)


def download(file: bytes, file_name: str, tmp_subfolder: str = "downloaded") -> str:
    folder = os.path.join(tempfile.gettempdir(), tmp_subfolder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    downloaded_path = os.path.join(folder, file_name)
    with open(downloaded_path, "wb") as f:
        f.write(file)
    return downloaded_path


def log_file_contents(path: str) -> None:
    logging.info(f"Logging file contents of {path}")
    with open(path, "r") as f:
        logging.info(f.read())


def get_sample_rate(wave_file_path: str) -> int:
    frame_rate = None
    try:
        with wave.open(wave_file_path, "rb") as wave_file:
            frame_rate = wave_file.getframerate()
        return frame_rate
    except wave.Error as e:
        if str(e) == "file does not start with RIFF id":
            log.exception(e)
            log.exception("Wavefile possibly corrupt!")
            raise Exception("Wavefile possibly corrupt!")


def upload_file_to_bucket(blob_name: str, path_to_file: str, bucket_name: str, storage_client: storage.Client = storage_client) -> str:
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)
    uri = f"gs://{bucket_name}/{blob_name}"
    return uri


def upload_content_to_new_blob(
    blob_name: str, content: Union[bytes, str], content_type: str, bucket_name: str, storage_client: storage.Client = storage_client
) -> str:
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(content, content_type)
    uri = f"gs://{bucket_name}/{blob_name}"
    return uri
