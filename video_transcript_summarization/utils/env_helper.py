import os

import ollama
from dotenv import load_dotenv

from video_transcript_summarization.model.i_type import IType


def load_environment_config(current_type: IType):
    """
    Load environment variables from .env file and return an IType instance with the loaded values.
    """
    load_dotenv("./video_transcript_summarization/envs/.env")

    llm_model = os.getenv("LLM_MODEL")
    if llm_model:
        current_type.model = llm_model

    target_language = os.getenv("TARGET_LANGUAGE")
    if target_language:
        current_type.target_language = target_language

    prompt_type = os.getenv("PROMPT_TYPE")
    if prompt_type:
        current_type.prompt_type = prompt_type

    parallel_api_calls = os.getenv("PARALLEL_API_CALLS")
    if parallel_api_calls:
        current_type.parallel_api_calls = int(parallel_api_calls)

    chunk_size = os.getenv("CHUNK_SIZE")
    if chunk_size:
        current_type.chunk_size = int(chunk_size)

    overlap_size = os.getenv("OVERLAP_SIZE")
    if overlap_size:
        current_type.overlap_size = int(overlap_size)

    max_output_tokens = os.getenv("MAX_OUTPUT_TOKENS")
    if max_output_tokens:
        current_type.max_output_tokens = int(max_output_tokens)

    whisper_model = os.getenv("WHISPER_MODEL")
    if whisper_model:
        current_type.whisper_model = whisper_model

    ollama_client_host = os.getenv("OLLAMA_CLIENT_HOST")
    if ollama_client_host:
        current_type.ollama_client = ollama.Client(
            host=ollama_client_host,
            verify=False
        )
