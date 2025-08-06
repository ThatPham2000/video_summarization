import re
import os

from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

from video_transcript_summarization.model.i_type import IType, seconds_to_time_format
from video_transcript_summarization.utils.utils import process_audio_file


class YoutubeType(IType):
    def __init__(self,
                 url,
                 use_youtube_captions=True):
        self.use_youtube_captions = use_youtube_captions
        super().__init__(url=url)

    def fetch_video(self):
        # clean YouTube url from timestamp
        self.url = re.sub('\&t=\d+s?', '', self.url)
        if self.use_youtube_captions:
            transcription_text, transcript_file_name = download_youtube_captions(self.url)
            self.transcription_text = transcription_text
            self.transcript_file_name = transcript_file_name
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


def download_youtube_captions(url):
    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    video_id = re.search(regex, url).group(1)
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except:
        for available_transcript in transcript_list:
            if available_transcript.is_translatable:
                transcript = available_transcript.translate('en').fetch()
                break

    transcription_text = ""
    for entry in transcript:
        start_time = seconds_to_time_format(entry['start'])
        transcription_text += f"{start_time} {entry['text'].strip()}\n"

    transcript_file_name = f"{video_id}_captions.md"

    with open(transcript_file_name, 'w', encoding='utf-8') as f:
        f.write(transcription_text)

    return transcription_text, transcript_file_name


def download_youtube_audio_only(url):
    yt = YouTube(url)
    audio_stream = yt.streams.get_audio_only()
    saved_path = audio_stream.download(output_path=".", skip_existing=True)
    return saved_path
