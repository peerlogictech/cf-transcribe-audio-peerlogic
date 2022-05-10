import logging
from typing import Dict, List, Tuple
from google.cloud import speech_v1p1beta1 as speech
import google.cloud.speech_v1p1beta1.types as types

log = logging.getLogger(__name__)


def transcribe_model_selection(
    source_uri: str,
    destination_uri: str,
    sample_rate_hertz: int = 8000,
    model: str = "phone_call",
    encoding: speech.RecognitionConfig.AudioEncoding = speech.RecognitionConfig.AudioEncoding.LINEAR16,
    # TODO: detect a different language?
    language_code: str = "en-US",
    enable_automatic_punctuation: bool = True,
    audio_channel_count: int = 2,
    enable_speaker_diarization: bool = True,
    diarization_speaker_count: int = 2,
    use_enhanced: bool = True,
    enable_separate_recognition_per_channel: bool = True,
) -> Tuple[List[str], Dict]:
    """
    Should asynchronously convert Speech to Text using speech_v1p1beta1.
    IMPORTANT: Even if destination_uri is
    gs://peerlogic-goog-speech-to-text-raw-extract-ana/bo6FTU5HbpsUmYn8TFofNq.json
    If processed a second time (with or without Object Versioning turned on),
    the blob name will look like this:
    bo6FTU5HbpsUmYn8TFofNq-2022-02-09T21-47-38_818394412+00-00.json
    """
    client = speech.SpeechClient()
    audio = speech.types.RecognitionAudio(uri=source_uri)
    output_config = speech.TranscriptOutputConfig(gcs_uri=destination_uri)
    config = speech.RecognitionConfig(
        sample_rate_hertz=sample_rate_hertz,
        model=model,
        encoding=encoding,
        language_code=language_code,
        enable_automatic_punctuation=enable_automatic_punctuation,
        audio_channel_count=audio_channel_count,
        enable_speaker_diarization=enable_speaker_diarization,
        diarization_speaker_count=diarization_speaker_count,
        use_enhanced=use_enhanced,
        enable_separate_recognition_per_channel=enable_separate_recognition_per_channel,
    )

    request_config = types.LongRunningRecognizeRequest(config=config, audio=audio, output_config=output_config)

    # TODO: Wrap in Future? seems to be still blocking when I test, for whatever reason
    client.long_running_recognize(request=request_config)


def get_channel_segregated_transcripts(transcript_raw_response):
    channel_1_text = ""
    channel_2_text = ""
    channel_transcripts = {1: channel_1_text, 2: channel_2_text}

    for item in transcript_raw_response["results"]:
        transcript = item["alternatives"][0]["transcript"]
        if transcript:
            channel_tag = item["channel_tag"]
            channel_transcripts[channel_tag] += transcript

    return channel_1_text, channel_2_text


def order_transcript_words_by_start_time(speech_to_text_response: Dict) -> List[str]:
    """Input: Transcript JSON. Output: Word list ordered by start time"""
    results_trancript_text = {}
    ordered_word_list = []
    repeated = {}
    time_list = []
    results = speech_to_text_response["results"]
    # storing words and their start_time in a dictionary with start_time as key
    for item in results:
        if item["alternatives"][0]["transcript"]:
            words = item["alternatives"][0]["words"]
            for info in words:
                word = info["word"]
                st_time = info["start_time"]
                st_time = float(st_time[:-1])
                if st_time not in results_trancript_text:
                    results_trancript_text[st_time] = word
                else:
                    repeated[st_time] = word
    # sorting the dictionary by key which is the start_time.
    results_trancript_text = dict(sorted(results_trancript_text.items()))
    repeated = dict(sorted(repeated.items()))
    time_list = list(results_trancript_text.keys())
    ordered_word_list = list(results_trancript_text.values())
    # creating the list which contains the words of transcript text in the correct order
    for k, v in repeated.items():
        index = len(time_list) - 1 - time_list[::-1].index(k)
        time_list.insert(index + 1, k)
        ordered_word_list.insert(index + 1, v)

    return ordered_word_list
