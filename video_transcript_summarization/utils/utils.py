import concurrent.futures
import glob
import os
import re
import subprocess
import time
import traceback

import ollama


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
    last_timestamp = '00:00:00'
    for chunk in text_chunks:
        timestamps = timestamp_pattern.findall(chunk)
        if timestamps:
            for timestamp in timestamps:
                # Remove each found timestamp from the chunk
                chunk = chunk.replace(timestamp, "")
            timestamp_ranges.append(timestamps[0])  # Assuming you want the first timestamp per chunk
            last_timestamp = timestamps[-1]
        else:
            timestamp_ranges.append(last_timestamp)  # If no timestamp found, use the last known timestamp
        cleaned_texts.append(chunk.strip())  # Strip to remove any leading/trailing whitespace
    return cleaned_texts, timestamp_ranges


def summarize(prompt, model, summary_prompt, ollama_client):
    if ollama_client is None:
        completion = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": prompt}
            ],
        )
        return completion.message.content

    completion = ollama_client.chat(
        model=model,
        messages=[
            {"role": "system", "content": summary_prompt},
            {"role": "user", "content": prompt}
        ],
    )
    return completion.message.content


def generate_action(model, paragraph, ollama_client):
    summary_prompt = '''You are a multilingual productivity assistant. Your task is to analyze a video summary in any language, extract all actionable items, and present them in a checklist.

**CRITICAL RULES:**
1.  **Detect Language:** Automatically identify the language of the provided summary.
2.  **Respond in Same Language:** Your entire output — the heading and the action items — MUST be in the detected language.
3.  **Translate Heading:** The heading must be the appropriate translation of the English phrase "## 📌 Actions to Take:".
4.  **Format as Checklist:** Each action must start with `- [ ]`.
5.  **No Actions:** If no specific actions can be extracted, respond with "No specific actions were mentioned." in the detected language.
6.  **No Additional Text:** Do not include any other text, explanations, or comments in your response.

---
**EXAMPLES**

**# Example 1: English**
**Input:** "In this meeting recap, the team agreed to finalize the quarterly report by Friday. Sarah will email the draft to John for review, and John will provide feedback by Wednesday."
**Output:**
## 📌 Actions to Take:
- [ ] Finalize the quarterly report by Friday.
- [ ] Sarah to email the draft report to John for review.
- [ ] John to provide feedback by Wednesday.

**# Example 2: French**
**Input:** "Résumé de la vidéo : Pour préparer votre voyage, vous devez d'abord réserver votre billet d'avion. Ensuite, confirmez votre réservation d'hôtel. N'oubliez pas de faire une photocopie de votre passeport."
**Output:**
## 📌 Actions à Entreprendre :
- [ ] Réserver le billet d'avion.
- [ ] Confirmer la réservation d'hôtel.
- [ ] Faire une photocopie du passeport.

**# Example 3: Japanese**
**Input:** 動画の要約：このチュートリアルでは、新しいソフトウェアのインストール方法を説明します。まず、公式サイトからファイルをダウンロードしてください。次に、インストーラーを実行し、最後にコンピュータを再起動します。
**Output:**
## 📌 実行すべきアクション：
- [ ] 公式サイトからファイルをダウンロードする。
- [ ] インストーラーを実行する。
- [ ] コンピュータを再起動する。

'''

    if ollama_client is None:
        completion = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": paragraph}
            ],
        )
        return completion.message.content

    completion = ollama_client.chat(
        model=model,
        messages=[
            {"role": "system", "content": summary_prompt},
            {"role": "user", "content": paragraph}
        ],
    )
    return completion.message.content


def process_and_summarize(text, chunk_size, overlap_size, parallel_api_calls, transcript_file_name, model,
                          summary_prompt, format_timestamp_link, ollama_client):
    texts = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap_size)]
    cleaned_texts, timestamp_ranges = extract_and_clean_timestamps(texts)
    summaries = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_api_calls) as executor:
        future_to_chunk = {executor.submit(summarize, text_chunk, model, summary_prompt, ollama_client): idx for
                           idx, text_chunk in
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
                future_to_chunk[executor.submit(summarize, texts[idx], model, summary_prompt, ollama_client)] = idx

    summaries.sort()  # Ensure summaries are in the correct order
    final_summary = "\n\n".join([summary for _, summary in summaries])
    overall = generate_overall_summary(model, final_summary, ollama_client)
    take_action = generate_action(model, final_summary, ollama_client)

    final_result = '## © 2025 PHAT, PHAV, TVAM\n\n' + overall + '\n\n' + take_action + '\n\n' + final_summary

    # Save the final summary
    final_name = transcript_file_name.replace(".md", "_FINAL.md")
    with open(final_name, 'w', encoding='utf-8') as f:
        f.write(final_result)

    return final_result


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


def generate_overall_summary(model, paragraph, ollama_client):
    system_prompt = '''You are a multilingual productivity assistant. Your task is to read the following paragraph and write a concise overall summary that captures its main idea.

**CRITICAL RULES:**
1.  **Detect Language:** Automatically identify the language of the provided summary.
2.  **Respond in Same Language:** Your entire output — the heading and the action items — MUST be in the detected language.
3.  **Translate Heading:** The heading must be the appropriate translation of the English phrase "## 📌 Overall:".
4.  **Format as Plain text:** The summary must be in plain text without any additional formatting.
5.  **No Additional Text:** Do not include any other text, explanations, or comments in your response.

Here is the paragraph:
'''

    if ollama_client is None:
        completion = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": paragraph}
            ],
        )
        return completion.message.content

    completion = ollama_client.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": paragraph}
        ],
    )
    return completion.message.content
