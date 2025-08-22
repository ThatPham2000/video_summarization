import json
import subprocess
import uuid

import whisper

from video_transcript_summarization.utils.utils import process_and_summarize, seconds_to_time_format


class IType(object):
    def __init__(self,
                 url,
                 model='llama3.2-vision:11b',
                 video_path_local=None,
                 supported_languages=None,
                 target_language='auto',
                 prompt_type='Summarization',
                 parallel_api_calls=30,
                 chunk_size=None,  # will be calculated based on video duration if not provided
                 overlap_size=20,
                 max_output_tokens=4096,
                 ollama_client=None,
                 whisper_model='turbo'
                 ):
        if supported_languages is None:
            supported_languages = ['en', 'vi', 'fr', 'de', 'it', 'gsw', 'rm', 'ja', 'zh',]

        self.uuid4 = uuid.uuid4().hex
        self.url = url
        self.model = model
        self.video_path_local = video_path_local
        self.supported_language = supported_languages
        self.target_language = target_language

        assert prompt_type in ['Summarization', 'Only grammar correction with highlights', 'Distill Wisdom',
                               'Questions and answers'], "Invalid prompt type."
        self.prompt_type = prompt_type

        self.transcription_text = ''
        self.transcript_file_name = ''

        # Parallel API calls (mind rate limits)
        self.parallel_api_calls = parallel_api_calls

        # Chunk size (tokens) (mind model context length). Higher = less granular summary.
        # Rule of thumb: 28k for 3h, 10k for 1h, 5k for 30min, 4k for shorter (1k for 6min).
        self.chunk_size = chunk_size

        # Overlap (tokens) between chunks
        self.overlap_size = overlap_size

        # Max output tokens of each chunk (mind model limits). Higher = less granular summary.
        # Rule of thumb: 4k, 2k or 1k depending on content density.
        # Only use for OpenAI
        self.max_output_tokens = max_output_tokens

        self.ollama_client = ollama_client

        self.whisper_model = whisper_model

    def fetch_video(self):
        pass

    def get_transcription_text(self):
        audio_files = []

        if self.video_path_local:
            # Single file transcription
            audio_files = [self.video_path_local]
        else:
            pass
            # Multiple chunk files
            # audio_files = audio_chunks

        for audio_file_path in audio_files:
            model_whisper = whisper.load_model(self.whisper_model)

            transcription = model_whisper.transcribe(
                audio_file_path,
                # beam_size=5,
                language=None if self.target_language == "auto" else self.target_language,
                # task="translate",
                # initial_prompt=initial_prompt or None
            )

            for segment in transcription["segments"]:
                start_time = seconds_to_time_format(segment['start'])
                self.transcription_text += f"{start_time} {segment['text'].strip()} "

        # Save the transcription
        self.transcript_file_name = self.uuid4 + '_transcription.md'
        with open(self.transcript_file_name, 'w', encoding='utf-8') as f:
            f.write(self.transcription_text)

    def summarize_and_elaborate(self):
        # load prompts from a local file
        with open('prompts.json', 'r') as f:
            prompts = json.load(f)
        summary_prompt = prompts[self.prompt_type]

        # calc chunk size based on model context length
        if self.chunk_size:
            chunk_size_per_seconds = 1000 / 6 / 60
            cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of',
                'default=noprint_wrappers=1:nokey=1', self.video_path_local
            ]
            duration = subprocess.check_output(cmd).decode().strip()
            print("Duration (seconds):", duration)
            self.chunk_size = (chunk_size_per_seconds * float(duration)).__floor__()
            print('Calculated chunk size:', self.chunk_size)

        return process_and_summarize(self.transcription_text, self.chunk_size, self.overlap_size,
                                     self.parallel_api_calls,
                                     self.transcript_file_name,
                                     self.model, summary_prompt,
                                     self.format_timestamp_link,
                                     self.ollama_client)

    def format_timestamp_link(self, timestamp):
        return f"{timestamp}"
