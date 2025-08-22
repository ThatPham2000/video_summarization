import os
import subprocess

from video_transcript_summarization.model.i_type import IType
from video_transcript_summarization.utils.utils import process_audio_file


class LocalType(IType):
    def __init__(self,
                 url,
                 model='llama3.2-vision:11b',
                 video_path_local=None,
                 supported_languages=None,
                 target_language='auto',
                 prompt_type='Summarization',
                 parallel_api_calls=30,
                 chunk_size=1000,
                 overlap_size=20,
                 max_output_tokens=4096,
                 ollama_client=None
                 ):
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
            ollama_client=ollama_client
        )

    def fetch_video(self):
        local_file_path = self.url
        video_path_local = f'{self.uuid4}_local_file_audio.wav'
        subprocess.run(['ffmpeg', '-y', '-i', local_file_path, '-vn', '-acodec', 'pcm_s16le',
                        '-ar', '16000', '-ac', '1', video_path_local], check=True)
        self.video_path_local = video_path_local
        # Process the audio file to reduce its size
        processed_audio_path = os.path.splitext(self.video_path_local)[0] + '_processed.mp3'
        process_audio_file(video_path_local, processed_audio_path)
        self.video_path_local = processed_audio_path  # Update to the processed file path
