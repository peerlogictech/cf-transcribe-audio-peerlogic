from typing import List


def format_transcript(word_list: List[str]) -> str:
    transcript_text = " ".join(word_list)
    transcript_text = transcript_text.strip('"')

    return transcript_text
