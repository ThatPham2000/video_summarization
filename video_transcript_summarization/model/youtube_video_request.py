import ollama
from pydantic import BaseModel

from video_transcript_summarization.model.youtube_type import YoutubeType
from video_transcript_summarization.utils.env_helper import load_environment_config


class YoutubeVideoRequest(BaseModel):
    url: str
    use_youtube_captions: bool = True
    target_language: str = 'auto'
    llm: str
    max_output_tokens: int
    ollama_client_host: str
    
    def __init__(self, **data):
        super().__init__(**data)
    
    def to_youtube_type(self):
        current_type = YoutubeType(url=self.url)
        load_environment_config(current_type)
        
        current_type.use_youtube_captions = self.use_youtube_captions
        current_type.target_language = self.target_language
        
        if self.llm:
            current_type.model = self.llm
        
        if self.ollama_client_host:
            current_type.ollama_client = ollama.Client(
                host=self.ollama_client_host,
                verify=False
            )

        if self.max_output_tokens:
            current_type.max_output_tokens = self.max_output_tokens

        return current_type