# import json
# import os
# import re
# import subprocess
# import uuid
#
# import whisper
#
# from video_transcript_summarization.utils.fetch_video import download_youtube_captions, download_youtube_audio_only, seconds_to_time_format
# from video_transcript_summarization.utils.process_audio_file import process_audio_file
# from video_transcript_summarization.utils.summarization_and_elaboration import process_and_summarize
#
# if __name__ == '__main__':
#     # <editor-fold desc="Configuration">
#     # ["YouTube Video", "Google Drive Video Link", "Dropbox Video Link", "Local File"]
#     Type = "Local File"
#     # URL = "https://www.youtube.com/watch?v=ngsxzZt5DoY"
#     URL='/Users/that.phamvan/Downloads/test-vi.mp3'
#     use_Youtube_captions = True
#
#     model = 'llama3.2-vision:11b'
#
#     supported_languages = ['en', 'vi']
#     language = 'auto'
#     initial_prompt = ""  # Initial Prompt for Whisper
#
#     # </editor-fold>
#
#     # <editor-fold desc="Video fetching">
#     skip_transcription = False
#     transcription_text = ""
#     textTimestamps = ""
#
#     transcript_file_name = uuid.uuid4().hex + '_captions.md'
#
#     if Type == "YouTube Video":
#         # clean youtube url from timestamp
#         URL = re.sub('\&t=\d+s?', '', URL)
#         if use_Youtube_captions:
#             transcription_text, transcript_file_name = download_youtube_captions(URL)
#             skip_transcription = True
#         else:
#             video_path_local = download_youtube_audio_only(URL)
#             # Process the audio file to reduce its size
#             processed_audio_path = os.path.splitext(video_path_local)[0] + '_processed.mp3'
#             process_audio_file(video_path_local, processed_audio_path)
#             video_path_local = processed_audio_path  # Update to the processed file path
#
#     elif Type == "Google Drive Video Link":
#         subprocess.run(['ffmpeg', '-y', '-i', "drive/MyDrive/" + URL, '-vn', '-acodec', 'pcm_s16le',
#                         '-ar', '16000', '-ac', '1', 'gdrive_audio.wav'], check=True)
#         video_path_local = "gdrive_audio.wav"
#         # Process the audio file to reduce its size
#         processed_audio_path = os.path.splitext(video_path_local)[0] + '_processed.mp3'
#         process_audio_file(video_path_local, processed_audio_path)
#         video_path_local = processed_audio_path  # Update to the processed file path
#
#     elif Type == "Dropbox Video Link":
#         subprocess.run(['wget', URL, '-O', 'dropbox_video.mp4'], check=True)
#         subprocess.run(['ffmpeg', '-y', '-i', 'dropbox_video.mp4', '-vn', '-acodec', 'pcm_s16le',
#                         '-ar', '16000', '-ac', '1', 'dropbox_video_audio.wav'], check=True)
#         video_path_local = "dropbox_video_audio.wav"
#         # Process the audio file to reduce its size
#         processed_audio_path = os.path.splitext(video_path_local)[0] + '_processed.mp3'
#         process_audio_file(video_path_local, processed_audio_path)
#         video_path_local = processed_audio_path  # Update to the processed file path
#
#     elif Type == "Local File":
#         local_file_path = URL
#         subprocess.run(['ffmpeg', '-y', '-i', local_file_path, '-vn', '-acodec', 'pcm_s16le',
#                         '-ar', '16000', '-ac', '1', 'local_file_audio.wav'], check=True)
#         video_path_local = "local_file_audio.wav"
#         # Process the audio file to reduce its size
#         processed_audio_path = os.path.splitext(video_path_local)[0] + '_processed.mp3'
#         process_audio_file(video_path_local, processed_audio_path)
#         video_path_local = processed_audio_path  # Update to the processed file path
#     # </editor-fold>
#
#     # <editor-fold desc="Transcription using Whisper">
#     if not skip_transcription:
#         transcription_text = ""
#
#         if video_path_local:
#             # Single file transcription
#             audio_files = [video_path_local]
#         else:
#             # Multiple chunk files
#             pass
#             # audio_files = audio_chunks
#
#         for audio_file_path in audio_files:
#             model_whisper = whisper.load_model("turbo")
#             # Local Whisper transcription
#             transcription = model_whisper.transcribe(
#                 audio_file_path,
#                 # beam_size=5,
#                 language=None if language == "auto" else language,
#                 task="translate",
#                 initial_prompt=initial_prompt or None
#             )
#
#             for segment in transcription["segments"]:
#                 start_time = seconds_to_time_format(segment['start'])
#                 transcription_text += f"{start_time} {segment['text'].strip()} "
#     else:
#         print("Using YouTube captions for transcription.")
#
#     # Save the transcription
#     if not skip_transcription:
#         transcript_file_name = 'transcription.md'
#         with open(transcript_file_name, 'w', encoding='utf-8') as f:
#             f.write(transcription_text)
#     else:
#         pass
#         # transcript_file_name = f"{video_id}_captions.md"
#     # </editor-fold>
#
#     # <editor-fold desc="Summarization and elaboration">
#
#     # ['Summarization', 'Only grammar correction with highlights','Distill Wisdom', 'Questions and answers']
#     prompt_type = "Summarization"
#
#     # Fetch prompts using curl
#     # prompts = json.loads(subprocess.check_output(
#     #     ['curl', '-s', 'https://raw.githubusercontent.com/martinopiaggi/summarize/refs/heads/main/prompts.json']))
#
#     # load prompts from a local file
#     with open('prompts.json', 'r') as f:
#         prompts = json.load(f)
#     summary_prompt = prompts[prompt_type]
#     print('dmm: ' + summary_prompt)
#
#     # Parallel API calls (mind rate limits)
#     parallel_api_calls = 30
#
#     # Chunk size (tokens) (mind model context length). Higher = less granular summary.
#     # Rule of thumb: 28k for 3h, 10k for 1h, 5k for 30min, 4k for shorter.
#     chunk_size = 2000
#
#     # Overlap (tokens) between chunks
#     overlap_size = 20
#
#     # Max output tokens of each chunk (mind model limits). Higher = less granular summary.
#     # Rule of thumb: 4k, 2k or 1k depending on content density.
#     max_output_tokens = 4096
#
#     process_and_summarize(transcription_text, chunk_size, overlap_size, parallel_api_calls, transcript_file_name, URL,
#                           Type, model, summary_prompt)
#     # </editor-fold>
