import re
import os

from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

from video_transcript_summarization.model.i_type import IType, seconds_to_time_format
from video_transcript_summarization.utils.utils import process_audio_file


class YoutubeType(IType):
    def __init__(self,
                 url,
                 use_youtube_captions=True,
                 model='llama3.2-vision:11b',
                 video_path_local=None,
                 supported_languages=None,
                 target_language='auto',
                 prompt_type='Summarization',
                 parallel_api_calls=30,
                 chunk_size=1000,
                 overlap_size=20,
                 max_output_tokens=4096,
                 ollama_client=None,
                 whisper_model='turbo'
                 ):
        self.use_youtube_captions = use_youtube_captions
        super().__init__(
            url=url,
            model=model,
            video_path_local=video_path_local,
            supported_languages=supported_languages,
            target_language=target_language,
            prompt_type=prompt_type,
            parallel_api_calls=parallel_api_calls,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            max_output_tokens=max_output_tokens,
            ollama_client=ollama_client,
            whisper_model=whisper_model
        )

    def fetch_video(self):
        # clean YouTube url from timestamp
        self.url = re.sub('\&t=\d+s?', '', self.url)
        if self.use_youtube_captions:
            transcription_text, transcript_file_name = download_youtube_captions(self.url,
                                                                                 [self.target_language] if self.target_language != 'auto' else self.supported_language)
            self.transcription_text = transcription_text
            self.transcript_file_name = transcript_file_name
            self.video_path_local = download_youtube_audio_only(self.url)
        else:
            video_path_local = download_youtube_audio_only(self.url)
            # Process the audio file to  reduce its size
            processed_audio_path = os.path.splitext(video_path_local)[0] + '_processed.mp3'
            process_audio_file(video_path_local, processed_audio_path)
            self.video_path_local = processed_audio_path  # Update to the processed file path

    def get_transcription_text(self):
        if self.use_youtube_captions:
            return
        super().get_transcription_text()

    def format_timestamp_link(self, timestamp):
        hours, minutes, seconds = map(int, timestamp.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return f"{timestamp} - {self.url}&t={total_seconds}"


def download_youtube_captions(url, language_codes):
    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    video_id = re.search(regex, url).group(1)

    lang_priority = language_codes
    ytt = YouTubeTranscriptApi()

    transcript_list = ytt.list(video_id)

    transcript = None
    try:
        transcript = ytt.fetch(video_id, languages=lang_priority)
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        transcript_list_language_codes = [available_transcript.language_code for available_transcript in transcript_list]

        for available_transcript in transcript_list:
            if available_transcript.is_translatable and lang_priority[0] in [language.language_code for language in available_transcript.translation_languages]:
                transcript = available_transcript.translate(lang_priority[0]).fetch()
                break

        if transcript is None:
            print("No suitable transcript found for the given language codes.")
            transcript = ytt.fetch(video_id, languages=transcript_list_language_codes)

    transcription_text = ""

    if transcript:
        for entry in transcript:
            start_time = seconds_to_time_format(entry.start)
            transcription_text += f"{start_time} {entry.text.strip()}\n"

    transcript_file_name = f"{video_id}_captions.md"

    with open(transcript_file_name, 'w', encoding='utf-8') as f:
        f.write(transcription_text)

    return transcription_text, transcript_file_name


def download_youtube_audio_only(url):
    yt = YouTube(url)
    audio_stream = yt.streams.get_audio_only()
    saved_path = audio_stream.download(output_path=".", skip_existing=True)
    return saved_path
