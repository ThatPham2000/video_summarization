import glob
import os
import re
import ollama
import concurrent.futures
import time
import traceback
import subprocess


def seconds_to_time_format(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


# Converts the audio file to MP3 with low sample rate and bitrate to reduce the file size (to stay in audio file API limits)
def process_audio_file(input_path, output_path):
    command_convert = [
        'ffmpeg', '-y', '-i', input_path,
        '-ar', str(8000),
        '-ac', str(1),
        '-b:a', '16k',
        output_path
    ]
    subprocess.run(command_convert, check=True)


def extract_and_clean_timestamps(text_chunks):
    timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2})')
    cleaned_texts = []
    timestamp_ranges = []
    for chunk in text_chunks:
        timestamps = timestamp_pattern.findall(chunk)
        if timestamps:
            for timestamp in timestamps:
                # Remove each found timestamp from the chunk
                chunk = chunk.replace(timestamp, "")
            timestamp_ranges.append(timestamps[0])  # Assuming you want the first timestamp per chunk
        else:
            timestamp_ranges.append("")
        cleaned_texts.append(chunk.strip())  # Strip to remove any leading/trailing whitespace
    return cleaned_texts, timestamp_ranges


def summarize(prompt, model, summary_prompt):
    completion = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": summary_prompt},
            {"role": "user", "content": prompt}
        ],
    )

    return completion.message.content


def process_and_summarize(text, chunk_size, overlap_size, parallel_api_calls, transcript_file_name, model,
                          summary_prompt, format_timestamp_link):
    texts = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap_size)]
    cleaned_texts, timestamp_ranges = extract_and_clean_timestamps(texts)
    summaries = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_api_calls) as executor:
        future_to_chunk = {executor.submit(summarize, text_chunk, model, summary_prompt): idx for idx, text_chunk in
                           enumerate(cleaned_texts)}
        for future in concurrent.futures.as_completed(future_to_chunk):
            idx = future_to_chunk[future]
            try:
                summarized_chunk = future.result()
                summary_piece = format_timestamp_link(timestamp_ranges[idx]) + "\n\n" + summarized_chunk
                summary_piece += "\n"
                summaries.append((idx, summary_piece))
            except Exception as exc:
                print(f'Chunk {idx} generated an exception: {exc}')
                print(traceback.format_exc())
                time.sleep(10)
                future_to_chunk[executor.submit(summarize, texts[idx], model, summary_prompt)] = idx

    summaries.sort()  # Ensure summaries are in the correct order
    final_summary = "\n\n".join([summary for _, summary in summaries])

    # Save the final summary
    final_name = transcript_file_name.replace(".md", "_FINAL.md")
    with open(final_name, 'w') as f:
        f.write(final_summary)

    return final_summary


def clear_intermediate_files():
    for file_path in glob.glob(os.path.join('.', '*.mp4')):
        os.remove(file_path)
    for file_path in glob.glob(os.path.join('.', '*.m4a')):
        os.remove(file_path)
    for file_path in glob.glob(os.path.join('.', '*.wav')):
        os.remove(file_path)
    for file_path in glob.glob(os.path.join('.', '*.mp3')):
        os.remove(file_path)
    for file_path in glob.glob(os.path.join('.', '*.md')):
        if '_FINAL.md' not in file_path and 'README.md' not in file_path:
            os.remove(file_path)
