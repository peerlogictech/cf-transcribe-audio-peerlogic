import base64
from typing import Optional
from config import BUCKET_AUDIO_PCM_ENCODED, BUCKET_GOOGLE_SPEECH_TO_TEXT_RAW_EXTRACT
import json
import logging

from flask import current_app, escape
from google.cloud import dlp_v2
from google.cloud import speech_v1p1beta1 as speech

from pydantic import BaseModel

from audio_conversion import wav_codec_to_pcm_s16le
from local_file_helpers import download, get_sample_rate, log_file_contents, upload_file_to_bucket
from peerlogic_api_client import PeerlogicAPIClient
from speech_to_text import transcribe_model_selection

logging.basicConfig(level=logging.NOTSET)

dlp = dlp_v2.DlpServiceClient()
speechClient = speech.SpeechClient()

log = logging.getLogger(__name__)

log.info(f"Cold started.")

# Declared at cold-start, but only initialized if/when the function executes
# We want to hold onto the bearer token for as long as possible to reduce lookups / calls
peerlogic_api_client: Optional[PeerlogicAPIClient] = None


class AudioReady(BaseModel):
    call_id: str
    partial_id: str
    audio_partial_id: str


def transcribe_audio_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    subject = request.args.get("subject", "World")
    subject = escape(subject)

    return f"Hello, {subject}!"


def transcribe_audio_pubsub(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """
    global peerlogic_api_client

    log = current_app.logger

    log.info(f"Started! Transcribe Audio - Stereo. Event: {event}, Context: {context}")

    log.info(f"Validating attributes and data.")
    data = base64.b64decode(event["data"]).decode("utf-8")
    data = json.loads(data)
    call_id = event.get("attributes", {}).get("call_id")
    audio_ready_event = AudioReady(**data)
    partial_id = audio_ready_event.partial_id
    audio_partial_id = audio_ready_event.audio_partial_id

    log_event_identifiers = f"call_id='{call_id}' audio_partial_id='{audio_partial_id}'"
    log.info(f"Audio Ready Event detected for {log_event_identifiers}")

    # This value is initialized only if (and when) the function is called
    if not peerlogic_api_client:
        log.info(f"Peerlogic API Client does not currently exist, logging in.")
        peerlogic_api_client = PeerlogicAPIClient()

    # for some reason this is not getting called and causing issues locally.
    # TODO: move back to above if statement
    peerlogic_api_client.login()

    # Get Wavfile
    log.info(f"Getting the call audio partials for audio_partial_id='{audio_partial_id}'")
    call_audio_partial_file = peerlogic_api_client.get_call_audio_partial_wavfile(call_id, partial_id, audio_partial_id)
    log.info(f"Got the call audio partial wavefile in memory for call_id='{call_id}' partial_id='{partial_id}' audio_partial_id='{audio_partial_id}")

    log.info(f"Saving file to tmp directory")
    downloaded_path = download(call_audio_partial_file, f"{partial_id}.wav")
    log.info(f"Saved file to tmp directory")

    log.info(f"Getting sample rate of wavefile to pass as Speech To Text arguments")
    try:
        sample_rate = get_sample_rate(downloaded_path)
    except Exception as e:
        log.exception(e)
        log.exception(f"Problem encountered with call_id audio: {call_id}")
        log_file_contents(downloaded_path)
        raise e
    log.info(f"Got sample rate of wavefile to pass as Speech To Text arguments")

    # Processing:
    log.info("Converting in memory wavefile to pcm")
    pcm_file_path, _ = wav_codec_to_pcm_s16le(downloaded_path)
    log.info("Converted in memory wavefile to pcm")

    # PCM is still wav extension: https://trac.ffmpeg.org/wiki/audio%20types
    log.info(f"Saving local pcm encoded file {partial_id}.wav to bucket {BUCKET_AUDIO_PCM_ENCODED}")
    pcm_file_gs_uri = upload_file_to_bucket(f"{partial_id}.wav", pcm_file_path, bucket_name=BUCKET_AUDIO_PCM_ENCODED)
    log.info(f"Saved local pcm encoded file to bucket {BUCKET_AUDIO_PCM_ENCODED}")

    # Transcribe and specify destination for output using call partial id
    destination_uri = f"gs://{BUCKET_GOOGLE_SPEECH_TO_TEXT_RAW_EXTRACT}/{call_id}-{partial_id}-{audio_partial_id}.json"
    log.info(f"Beginning long-running transcription of pcm encoded wave file using Google Speech to Text.")
    transcribe_model_selection(pcm_file_gs_uri, destination_uri, sample_rate_hertz=sample_rate)
    # TODO: See if timeouts mean failure and this will reprocess from dead-letter queue
    # Otherwise, figure out how to not make this blocking
    log.info(f"Finished calling long-running transcription of pcm encoded file using Google Speech to Text with destination uri: {destination_uri}")
