import os
import tempfile


def wav_codec_to_pcm_s16le(path: str, encoded_subfolder: str = "encoded"):
    file_basename = os.path.basename(path)
    encoded_folderpath = os.path.join(tempfile.gettempdir(), encoded_subfolder)
    if not os.path.exists(encoded_folderpath):
        os.makedirs(encoded_folderpath)
    encoded_filepath = os.path.join(tempfile.gettempdir(), encoded_subfolder, file_basename)
    os.system(f"ffmpeg -y -i {path} -t 1800 -c:a pcm_s16le {encoded_filepath}")
    return encoded_filepath, file_basename
